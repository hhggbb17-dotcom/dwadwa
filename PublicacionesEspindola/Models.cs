namespace PublicacionesEspindola;

public sealed class AppData
{
    public int NextCustomerId { get; set; } = 1;
    public int NextSupplierId { get; set; } = 1;
    public int NextPublicationId { get; set; } = 1;
    public int NextEditionId { get; set; } = 1;
    public int NextMovementId { get; set; } = 1;
    public int NextPaymentId { get; set; } = 1;
    public int NextRouteId { get; set; } = 1;
    public int NextUserId { get; set; } = 1;
    public List<AppUser> Users { get; set; } = [];
    public List<Customer> Customers { get; set; } = [];
    public List<Supplier> Suppliers { get; set; } = [];
    public List<Publication> Publications { get; set; } = [];
    public List<Edition> Editions { get; set; } = [];
    public List<Movement> Movements { get; set; } = [];
    public List<Payment> Payments { get; set; } = [];
    public List<DeliveryRoute> Routes { get; set; } = [];
}

public sealed class AppUser
{
    public int Id { get; set; }
    public string Username { get; set; } = "";
    public string DisplayName { get; set; } = "";
    public string Role { get; set; } = "Operator";
    public string Salt { get; set; } = "";
    public string PasswordHash { get; set; } = "";
    public bool Active { get; set; } = true;
}

public sealed class Customer
{
    public int Id { get; set; }
    public string Code { get; set; } = "";
    public string Name { get; set; } = "";
    public string Rfc { get; set; } = "";
    public string Phone { get; set; } = "";
    public string Email { get; set; } = "";
    public string Address { get; set; } = "";
    public string City { get; set; } = "";
    public decimal CreditLimit { get; set; }
    public decimal Balance { get; set; }
    public decimal DiscountPercent { get; set; }
    public int? RouteId { get; set; }
    public bool Active { get; set; } = true;
}

public sealed class Supplier
{
    public int Id { get; set; }
    public string Code { get; set; } = "";
    public string Name { get; set; } = "";
    public string Rfc { get; set; } = "";
    public string Phone { get; set; } = "";
    public string Email { get; set; } = "";
    public string Address { get; set; } = "";
    public decimal Balance { get; set; }
    public bool Active { get; set; } = true;
}

public sealed class Publication
{
    public int Id { get; set; }
    public string Code { get; set; } = "";
    public string Title { get; set; } = "";
    public int SupplierId { get; set; }
    public string Barcode { get; set; } = "";
    public decimal TaxPercent { get; set; }
    public bool Monitored { get; set; }
    public bool Active { get; set; } = true;
}

public sealed class Edition
{
    public int Id { get; set; }
    public int PublicationId { get; set; }
    public string Number { get; set; } = "";
    public string Name { get; set; } = "";
    public string Barcode { get; set; } = "";
    public DateTime ArrivalDate { get; set; } = DateTime.Today;
    public DateTime? ReturnDeadline { get; set; }
    public decimal Price { get; set; }
    public int Stock { get; set; }
    public int Reserved { get; set; }
    public bool Active { get; set; } = true;
}

public sealed class Movement
{
    public int Id { get; set; }
    public string Folio { get; set; } = "";
    public string Type { get; set; } = "Sale";
    public DateTime CreatedAt { get; set; } = DateTime.Now;
    public int? CustomerId { get; set; }
    public int? SupplierId { get; set; }
    public int UserId { get; set; }
    public string PaymentType { get; set; } = "Cash";
    public decimal Subtotal { get; set; }
    public decimal Discount { get; set; }
    public decimal Tax { get; set; }
    public decimal Total { get; set; }
    public string Notes { get; set; } = "";
    public List<MovementLine> Lines { get; set; } = [];
}

public sealed class MovementLine
{
    public int EditionId { get; set; }
    public int Quantity { get; set; }
    public decimal UnitPrice { get; set; }
    public decimal DiscountPercent { get; set; }
    public decimal TaxPercent { get; set; }
    public decimal Total { get; set; }
}

public sealed class Payment
{
    public int Id { get; set; }
    public int CustomerId { get; set; }
    public DateTime CreatedAt { get; set; } = DateTime.Now;
    public decimal Amount { get; set; }
    public string Method { get; set; } = "Cash";
    public string Reference { get; set; } = "";
    public int UserId { get; set; }
}

public sealed class DeliveryRoute
{
    public int Id { get; set; }
    public string Name { get; set; } = "";
    public string Zone { get; set; } = "";
    public string DeliveryDay { get; set; } = "";
    public bool Active { get; set; } = true;
}

public record LoginRequest(string Username, string Password);
public record UserRequest(string Username, string DisplayName, string Role, string Password);
public record MovementRequest(int? CustomerId, int? SupplierId, string PaymentType, string? Notes, List<MovementLineRequest> Lines);
public record MovementLineRequest(int EditionId, int Quantity, decimal? UnitPrice, decimal DiscountPercent);
public record PaymentRequest(int CustomerId, decimal Amount, string Method, string? Reference);
