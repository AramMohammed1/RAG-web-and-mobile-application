
var builder = WebApplication.CreateBuilder(args);

#region Cors
var AllowSpecificOrigins = "_AllowFrontEnd";
builder.Services.AddCors(options =>
{
    options.AddPolicy(name: AllowSpecificOrigins,
                      policy =>
                      {
                          policy.WithOrigins("http://localhost:5173")
 
                          .AllowAnyHeader()
                          .AllowAnyMethod()
                          .AllowCredentials();
});
});
#endregion
builder.Services.AddReverseProxy()
    .LoadFromConfig(builder.Configuration.GetSection("ReverseProxy"));

var app = builder.Build();

app.UseCors(AllowSpecificOrigins);


app.MapReverseProxy();
app.Run();
