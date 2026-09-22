using PublicacionesEspindola;

var builder = WebApplication.CreateBuilder(args);
builder.Services.AddSingleton<AppStore>();
builder.Services.AddSingleton<SessionService>();
builder.WebHost.UseUrls("http://127.0.0.1:5188");

var app = builder.Build();
app.UseDefaultFiles();
app.UseStaticFiles();

app.Use(async (context, next) =>
{
    if (context.Request.Path.StartsWithSegments("/api") && context.Request.Path != "/api/auth/login")
    {
        var sessions = context.RequestServices.GetRequiredService<SessionService>();
        var store = context.RequestServices.GetRequiredService<AppStore>();
        var token = context.Request.Headers.Authorization.ToString().Replace("Bearer ", "", StringComparison.OrdinalIgnoreCase);
        var userId = sessions.Resolve(token);
        var user = userId is null ? null : store.Read(d => d.Users.FirstOrDefault(x => x.Id == userId && x.Active));
        if (user is null) { context.Response.StatusCode = 401; await context.Response.WriteAsJsonAsync(new { error = "Sesión no válida" }); return; }
        context.Items["user"] = user;
        context.Items["token"] = token;
    }
    await next();
});

app.MapPost("/api/auth/login", (LoginRequest request, AppStore store, SessionService sessions) =>
{
    var normalized = request.Username.Trim().ToUpperInvariant();
    var user = store.Read(d => d.Users.FirstOrDefault(x => x.Active && x.Username.ToUpper() == normalized));
    if (user is null || !AppStore.VerifyPassword(user, request.Password)) return Results.Unauthorized();
    return Results.Ok(new { token = sessions.Create(user.Id), user = PublicUser(user) });
});
app.MapGet("/api/auth/me", (HttpContext c) => Results.Ok(PublicUser(User(c))));
app.MapPost("/api/auth/logout", (HttpContext c, SessionService sessions) => { sessions.Remove(c.Items["token"]?.ToString()); return Results.Ok(); });

app.MapGet("/api/dashboard", (AppStore store) => Results.Ok(store.Read(d =>
{
    var today = DateTime.Today;
    return new
    {
        salesToday = d.Movements.Where(x => x.Type == "Sale" && x.CreatedAt.Date == today).Sum(x => x.Total),
        returnsToday = d.Movements.Where(x => x.Type == "Return" && x.CreatedAt.Date == today).Sum(x => x.Total),
        receivables = d.Customers.Sum(x => x.Balance),
        inventoryUnits = d.Editions.Sum(x => x.Stock),
        inventoryValue = d.Editions.Sum(x => x.Stock * x.Price),
        activeCustomers = d.Customers.Count(x => x.Active),
        lowStock = d.Editions.Count(x => x.Active && x.Stock <= 5),
        recent = d.Movements.OrderByDescending(x => x.CreatedAt).Take(8).ToList()
    };
})));

app.MapGet("/api/customers", (AppStore s) => s.Read(d => d.Customers.OrderBy(x => x.Name).ToList()));
app.MapPost("/api/customers", (Customer item, AppStore s) =>
{
    if (string.IsNullOrWhiteSpace(item.Name)) return Results.BadRequest(new { error = "El nombre es obligatorio" });
    return Results.Ok(s.Write(d => { item.Id = d.NextCustomerId++; item.Code = string.IsNullOrWhiteSpace(item.Code) ? $"CLI-{item.Id:0000}" : item.Code.Trim(); d.Customers.Add(item); return item; }));
});
app.MapPut("/api/customers/{id:int}", (int id, Customer input, AppStore s) => UpdateEntity(s, d => d.Customers, id, input, x => x.Id, (old, value) =>
{
    value.Id = old.Id; value.Balance = old.Balance; return value;
}));

app.MapGet("/api/suppliers", (AppStore s) => s.Read(d => d.Suppliers.OrderBy(x => x.Name).ToList()));
app.MapPost("/api/suppliers", (Supplier item, AppStore s) =>
{
    if (string.IsNullOrWhiteSpace(item.Name)) return Results.BadRequest(new { error = "El nombre es obligatorio" });
    return Results.Ok(s.Write(d => { item.Id = d.NextSupplierId++; item.Code = string.IsNullOrWhiteSpace(item.Code) ? $"PROV-{item.Id:0000}" : item.Code.Trim(); d.Suppliers.Add(item); return item; }));
});

app.MapGet("/api/publications", (AppStore s) => s.Read(d => d.Publications.OrderBy(x => x.Title).ToList()));
app.MapPost("/api/publications", (Publication item, AppStore s) =>
{
    if (string.IsNullOrWhiteSpace(item.Title) || item.SupplierId <= 0) return Results.BadRequest(new { error = "Título y proveedor son obligatorios" });
    return Results.Ok(s.Write(d => { item.Id = d.NextPublicationId++; item.Code = string.IsNullOrWhiteSpace(item.Code) ? $"REV-{item.Id:0000}" : item.Code.Trim(); d.Publications.Add(item); return item; }));
});

app.MapGet("/api/editions", (AppStore s) => s.Read(d => d.Editions.OrderByDescending(x => x.ArrivalDate).ToList()));
app.MapPost("/api/editions", (Edition item, AppStore s) =>
{
    if (item.PublicationId <= 0 || string.IsNullOrWhiteSpace(item.Number) || item.Price < 0 || item.Stock < 0) return Results.BadRequest(new { error = "Publicación, número, precio y existencia válidos son obligatorios" });
    return Results.Ok(s.Write(d => { item.Id = d.NextEditionId++; d.Editions.Add(item); return item; }));
});

app.MapGet("/api/movements", (string? type, AppStore s) => s.Read(d => d.Movements.Where(x => string.IsNullOrWhiteSpace(type) || x.Type == type).OrderByDescending(x => x.CreatedAt).Take(500).ToList()));
app.MapPost("/api/movements/{type}", (string type, MovementRequest request, HttpContext c, AppStore s) =>
{
    var normalized = type.ToLowerInvariant() switch { "sales" => "Sale", "purchases" => "Purchase", "returns" => "Return", _ => "" };
    if (normalized == "" || request.Lines.Count == 0) return Results.BadRequest(new { error = "Movimiento o partidas no válidas" });
    try
    {
        var movement = s.Write(d =>
        {
            if (normalized is "Sale" or "Return" && request.CustomerId is null) throw new InvalidOperationException("Selecciona un cliente");
            if (normalized == "Purchase" && request.SupplierId is null) throw new InvalidOperationException("Selecciona un proveedor");
            var result = new Movement { Id = d.NextMovementId++, Type = normalized, Folio = $"{normalized[..1]}-{DateTime.Now:yyMMdd}-{d.NextMovementId - 1:0000}", CustomerId = request.CustomerId, SupplierId = request.SupplierId, PaymentType = request.PaymentType, Notes = request.Notes ?? "", UserId = User(c).Id };
            foreach (var line in request.Lines)
            {
                if (line.Quantity <= 0) throw new InvalidOperationException("La cantidad debe ser mayor que cero");
                var edition = d.Editions.FirstOrDefault(x => x.Id == line.EditionId) ?? throw new InvalidOperationException("Edición no encontrada");
                var publication = d.Publications.First(x => x.Id == edition.PublicationId);
                if (normalized == "Sale" && edition.Stock < line.Quantity) throw new InvalidOperationException($"Existencia insuficiente para {edition.Name}");
                var price = line.UnitPrice ?? edition.Price;
                var gross = price * line.Quantity;
                var discount = decimal.Round(gross * line.DiscountPercent / 100m, 2);
                var tax = decimal.Round((gross - discount) * publication.TaxPercent / 100m, 2);
                result.Subtotal += gross; result.Discount += discount; result.Tax += tax;
                result.Lines.Add(new MovementLine { EditionId = edition.Id, Quantity = line.Quantity, UnitPrice = price, DiscountPercent = line.DiscountPercent, TaxPercent = publication.TaxPercent, Total = gross - discount + tax });
                edition.Stock += normalized == "Purchase" || normalized == "Return" ? line.Quantity : -line.Quantity;
            }
            result.Total = result.Subtotal - result.Discount + result.Tax;
            if (normalized == "Sale" && request.PaymentType.Equals("Credit", StringComparison.OrdinalIgnoreCase)) d.Customers.First(x => x.Id == request.CustomerId).Balance += result.Total;
            if (normalized == "Return") d.Customers.First(x => x.Id == request.CustomerId).Balance = Math.Max(0, d.Customers.First(x => x.Id == request.CustomerId).Balance - result.Total);
            if (normalized == "Purchase") d.Suppliers.First(x => x.Id == request.SupplierId).Balance += result.Total;
            d.Movements.Add(result); return result;
        });
        return Results.Ok(movement);
    }
    catch (InvalidOperationException ex) { return Results.BadRequest(new { error = ex.Message }); }
});

app.MapGet("/api/payments", (AppStore s) => s.Read(d => d.Payments.OrderByDescending(x => x.CreatedAt).Take(500).ToList()));
app.MapPost("/api/payments", (PaymentRequest request, HttpContext c, AppStore s) =>
{
    if (request.Amount <= 0) return Results.BadRequest(new { error = "El abono debe ser mayor que cero" });
    try { return Results.Ok(s.Write(d => { var customer = d.Customers.FirstOrDefault(x => x.Id == request.CustomerId) ?? throw new InvalidOperationException("Cliente no encontrado"); var payment = new Payment { Id = d.NextPaymentId++, CustomerId = customer.Id, Amount = request.Amount, Method = request.Method, Reference = request.Reference ?? "", UserId = User(c).Id }; customer.Balance = Math.Max(0, customer.Balance - request.Amount); d.Payments.Add(payment); return payment; })); }
    catch (InvalidOperationException ex) { return Results.BadRequest(new { error = ex.Message }); }
});

app.MapGet("/api/routes", (AppStore s) => s.Read(d => d.Routes.OrderBy(x => x.Name).ToList()));
app.MapPost("/api/routes", (DeliveryRoute item, AppStore s) =>
{
    if (string.IsNullOrWhiteSpace(item.Name)) return Results.BadRequest(new { error = "El nombre es obligatorio" });
    return Results.Ok(s.Write(d => { item.Id = d.NextRouteId++; d.Routes.Add(item); return item; }));
});

app.MapGet("/api/users", (HttpContext c, AppStore s) => IsAdmin(c) ? Results.Ok(s.Read(d => d.Users.Select(PublicUser).ToList())) : Results.Forbid());
app.MapPost("/api/users", (UserRequest request, HttpContext c, AppStore s) =>
{
    if (!IsAdmin(c)) return Results.Forbid();
    if (string.IsNullOrWhiteSpace(request.Username) || request.Password.Length < 4) return Results.BadRequest(new { error = "Usuario y contraseña de al menos 4 caracteres son obligatorios" });
    var credentials = AppStore.HashPassword(request.Password);
    return Results.Ok(s.Write(d => { if (d.Users.Any(x => x.Username.Equals(request.Username, StringComparison.OrdinalIgnoreCase))) throw new InvalidOperationException("El usuario ya existe"); var user = new AppUser { Id = d.NextUserId++, Username = request.Username.Trim().ToUpperInvariant(), DisplayName = request.DisplayName.Trim(), Role = request.Role == "Admin" ? "Admin" : "Operator", Salt = credentials.Salt, PasswordHash = credentials.Hash }; d.Users.Add(user); return PublicUser(user); }));
});

app.MapFallbackToFile("index.html");
app.Run();

static AppUser User(HttpContext c) => (AppUser)c.Items["user"]!;
static bool IsAdmin(HttpContext c) => User(c).Role == "Admin";
static object PublicUser(AppUser u) => new { u.Id, u.Username, u.DisplayName, u.Role, u.Active };
static IResult UpdateEntity<T>(AppStore store, Func<AppData, List<T>> list, int id, T input, Func<T, int> key, Func<T, T, T> merge)
{
    var result = store.Write(d => { var items = list(d); var index = items.FindIndex(x => key(x) == id); if (index < 0) return default; items[index] = merge(items[index], input); return items[index]; });
    return result is null ? Results.NotFound() : Results.Ok(result);
}
