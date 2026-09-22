using System.Security.Cryptography;
using System.Text.Json;

namespace PublicacionesEspindola;

public sealed class AppStore
{
    private readonly object _gate = new();
    private readonly string _path;
    private readonly JsonSerializerOptions _json = new(JsonSerializerDefaults.Web) { WriteIndented = true };
    public AppData Data { get; private set; }

    public AppStore(IWebHostEnvironment environment)
    {
        var dataDir = Path.Combine(environment.ContentRootPath, "data");
        Directory.CreateDirectory(dataDir);
        _path = Path.Combine(dataDir, "store.json");
        Data = Load();
        if (Data.Users.Count == 0) Seed();
    }

    private AppData Load()
    {
        if (!File.Exists(_path)) return new AppData();
        try { return JsonSerializer.Deserialize<AppData>(File.ReadAllText(_path), _json) ?? new AppData(); }
        catch { return new AppData(); }
    }

    private void Seed()
    {
        Data.Users.AddRange([
            new AppUser { Id = Data.NextUserId++, Username = "SISTEMAS", DisplayName = "Administrador", Role = "Admin", Salt = "W0e6vpkSOQTox5bsblWeYQ==", PasswordHash = "zlR5if8embaYwuH4K76hgnYqEg4NV+XkWeT0aazylOg=" },
            new AppUser { Id = Data.NextUserId++, Username = "CARLOS ESPINDOLA", DisplayName = "Carlos Espindola", Role = "Operator", Salt = "tr1Y79uBct+iMu8wZVCr6g==", PasswordHash = "rd5adFdTUjocqFaAe47X3E5QrZ9XC8V3EYieAU3kPkE=" }
        ]);
        var supplier = new Supplier { Id = Data.NextSupplierId++, Code = "PROV-001", Name = "Proveedor editorial", Active = true };
        Data.Suppliers.Add(supplier);
        var publication = new Publication { Id = Data.NextPublicationId++, Code = "REV-001", Title = "Publicación de ejemplo", SupplierId = supplier.Id, Barcode = "750000000001", TaxPercent = 0, Active = true };
        Data.Publications.Add(publication);
        Data.Editions.Add(new Edition { Id = Data.NextEditionId++, PublicationId = publication.Id, Number = "001", Name = "Edición inicial", Barcode = "7500000000011", Price = 60, Stock = 25, ArrivalDate = DateTime.Today, ReturnDeadline = DateTime.Today.AddDays(30) });
        Data.Customers.Add(new Customer { Id = Data.NextCustomerId++, Code = "CLI-001", Name = "Cliente de mostrador", CreditLimit = 5000, Active = true });
        Data.Routes.Add(new DeliveryRoute { Id = Data.NextRouteId++, Name = "Ruta Centro", Zone = "Centro", DeliveryDay = "Lunes" });
        SaveUnsafe();
    }

    public T Read<T>(Func<AppData, T> action) { lock (_gate) return action(Data); }
    public T Write<T>(Func<AppData, T> action) { lock (_gate) { var result = action(Data); SaveUnsafe(); return result; } }
    public void Write(Action<AppData> action) { lock (_gate) { action(Data); SaveUnsafe(); } }

    private void SaveUnsafe()
    {
        var temp = _path + ".tmp";
        File.WriteAllText(temp, JsonSerializer.Serialize(Data, _json));
        File.Move(temp, _path, true);
    }

    public static bool VerifyPassword(AppUser user, string password)
    {
        var actual = Rfc2898DeriveBytes.Pbkdf2(password, Convert.FromBase64String(user.Salt), 100_000, HashAlgorithmName.SHA1, 32);
        return CryptographicOperations.FixedTimeEquals(actual, Convert.FromBase64String(user.PasswordHash));
    }

    public static (string Salt, string Hash) HashPassword(string password)
    {
        var salt = RandomNumberGenerator.GetBytes(16);
        var hash = Rfc2898DeriveBytes.Pbkdf2(password, salt, 100_000, HashAlgorithmName.SHA1, 32);
        return (Convert.ToBase64String(salt), Convert.ToBase64String(hash));
    }
}

public sealed class SessionService
{
    private readonly Dictionary<string, (int UserId, DateTime Expires)> _sessions = [];
    private readonly object _gate = new();
    public string Create(int userId)
    {
        var token = Convert.ToHexString(RandomNumberGenerator.GetBytes(32));
        lock (_gate) _sessions[token] = (userId, DateTime.UtcNow.AddHours(12));
        return token;
    }
    public int? Resolve(string? token)
    {
        if (string.IsNullOrWhiteSpace(token)) return null;
        lock (_gate)
        {
            if (!_sessions.TryGetValue(token, out var session) || session.Expires < DateTime.UtcNow) { _sessions.Remove(token); return null; }
            return session.UserId;
        }
    }
    public void Remove(string? token) { if (token is not null) lock (_gate) _sessions.Remove(token); }
}
