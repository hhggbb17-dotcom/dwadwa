using System.Text.Json;
using FirebirdSql.Data.FirebirdClient;
using PublicacionesEspindola;

if (args.Length < 2)
{
    Console.Error.WriteLine("Uso: Migrador <ruta-fdb> <store-json>");
    return 2;
}

var database = Path.GetFullPath(args[0]);
var output = Path.GetFullPath(args[1]);
if (!File.Exists(database)) { Console.Error.WriteLine($"No existe la base: {database}"); return 3; }

var data = new AppData();
data.Users.AddRange([
    new AppUser { Id = data.NextUserId++, Username = "SISTEMAS", DisplayName = "Administrador", Role = "Admin", Salt = "W0e6vpkSOQTox5bsblWeYQ==", PasswordHash = "zlR5if8embaYwuH4K76hgnYqEg4NV+XkWeT0aazylOg=" },
    new AppUser { Id = data.NextUserId++, Username = "CARLOS ESPINDOLA", DisplayName = "Carlos Espindola", Role = "Operator", Salt = "tr1Y79uBct+iMu8wZVCr6g==", PasswordHash = "rd5adFdTUjocqFaAe47X3E5QrZ9XC8V3EYieAU3kPkE=" }
]);

var cs = new FbConnectionStringBuilder { DataSource = "localhost", Port = 3050, Database = database, UserID = "SYSDBA", Password = "masterkey", Dialect = 1, Charset = "NONE", Pooling = false }.ToString();
await using var connection = new FbConnection(cs);
await connection.OpenAsync();
Console.WriteLine("Conexión Firebird establecida.");

await Read("select CLAVCLIE, NOMBCLIE, RFCCLIE, TELECLIE, DIRECLIE, CIUDCLIE, LIMICREDCLIE, SALDACTUCLIE, DESCCLIE, STATCLIE from CLIENTES order by CLAVCLIE", r =>
{
    var id = I(r,0); data.Customers.Add(new Customer { Id=id, Code=id.ToString(), Name=S(r,1), Rfc=S(r,2), Phone=S(r,3), Address=S(r,4), City=S(r,5), CreditLimit=D(r,6), Balance=D(r,7), DiscountPercent=D(r,8), Active=I(r,9)==1 });
    data.NextCustomerId=Math.Max(data.NextCustomerId,id+1);
});
await Read("select CLAVPROV, NOMBPROV, RFCPROV, TELEPROV, EMAIPROV, DIREPROV, CIUDPROV, SALDPROV, STATPROV from PROVEEDORES order by CLAVPROV", r =>
{
    var id=I(r,0); data.Suppliers.Add(new Supplier { Id=id, Code=id.ToString(), Name=S(r,1), Rfc=S(r,2), Phone=S(r,3), Email=S(r,4), Address=$"{S(r,5)} {S(r,6)}".Trim(), Balance=D(r,7), Active=I(r,8)==1 }); data.NextSupplierId=Math.Max(data.NextSupplierId,id+1);
});

var publicationIds = new Dictionary<string,int>(StringComparer.OrdinalIgnoreCase);
await Read("select CLAVREVI, TITUREVI, CLAVPROVREVI, CODIBARRREVI, IVAREVI, MONIREVI, STATREVI from REVISTAS order by CLAVREVI", r =>
{
    var legacy=S(r,0); var id=data.NextPublicationId++; publicationIds[legacy]=id; data.Publications.Add(new Publication { Id=id, Code=legacy, Title=S(r,1), SupplierId=I(r,2), Barcode=S(r,3), TaxPercent=I(r,4)==1?16:0, Monitored=S(r,5).Equals("SI",StringComparison.OrdinalIgnoreCase), Active=I(r,6)==1 });
});

const string editionSql = @"select E.CLAVEDIC, E.CLAVREVIEDIC, E.NUMEEDIC, E.NOMBEDIC, E.CODIBARREDIC, E.FECHENTREDIC, E.FECHVENCCLIEEDIC, E.PRECEDIC, E.STATEDIC, (X.EXISACTUBODEEXIS + X.EXISACTUDEVOEXIS) STOCK from EDICIONES E join EXISTENCIAS X on X.CLAVEDICEXIS=E.CLAVEDIC and X.CLAVREVIEXIS=E.CLAVREVIEDIC where (X.EXISACTUBODEEXIS + X.EXISACTUDEVOEXIS)>0 order by E.CLAVREVIEDIC,E.NUMEEDIC";
await Read(editionSql, r =>
{
    if(!publicationIds.TryGetValue(S(r,1),out var publicationId))return; data.Editions.Add(new Edition { Id=data.NextEditionId++, PublicationId=publicationId, Number=I(r,2).ToString(), Name=string.IsNullOrWhiteSpace(S(r,3))?S(r,0):S(r,3), Barcode=S(r,4), ArrivalDate=DT(r,5)??DateTime.Today, ReturnDeadline=DT(r,6), Price=D(r,7), Active=I(r,8)==1, Stock=I(r,9) });
});

try
{
    await Read("select CLAVRUTA, NOMBRUTA, ZONARUTA, DIARUTA, STATRUTA from RUTAS order by CLAVRUTA", r => { var id=I(r,0); data.Routes.Add(new DeliveryRoute { Id=id, Name=S(r,1), Zone=S(r,2), DeliveryDay=S(r,3), Active=I(r,4)==1 }); data.NextRouteId=Math.Max(data.NextRouteId,id+1); });
}
catch (FbException) { data.Routes.Add(new DeliveryRoute { Id=data.NextRouteId++, Name="Ruta general", Zone="", DeliveryDay="" }); }

Directory.CreateDirectory(Path.GetDirectoryName(output)!);
if (File.Exists(output)) File.Copy(output, Path.Combine(Path.GetDirectoryName(output)!, "store.pre-import.json"), true);
var options = new JsonSerializerOptions(JsonSerializerDefaults.Web) { WriteIndented = true };
await File.WriteAllTextAsync(output + ".tmp", JsonSerializer.Serialize(data, options));
File.Move(output + ".tmp", output, true);
Console.WriteLine($"Migración terminada: {data.Customers.Count} clientes, {data.Suppliers.Count} proveedores, {data.Publications.Count} publicaciones y {data.Editions.Count} ediciones con existencia.");
return 0;

async Task Read(string sql, Action<FbDataReader> map)
{
    await using var command = new FbCommand(sql, connection); command.CommandTimeout=0;
    await using var reader = await command.ExecuteReaderAsync();
    while (await reader.ReadAsync()) map(reader);
}
static string S(FbDataReader r,int i)=>r.IsDBNull(i)?"":Convert.ToString(r.GetValue(i))?.Trim()??"";
static int I(FbDataReader r,int i)=>r.IsDBNull(i)?0:Convert.ToInt32(r.GetValue(i));
static decimal D(FbDataReader r,int i)=>r.IsDBNull(i)?0:Convert.ToDecimal(r.GetValue(i));
static DateTime? DT(FbDataReader r,int i)=>r.IsDBNull(i)?null:Convert.ToDateTime(r.GetValue(i));
