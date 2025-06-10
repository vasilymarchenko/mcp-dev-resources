public class DefaultCompositeCustomization : CompositeCustomization
{
    public DefaultCompositeCustomization(Type? t)
        : base(
              new AutoNSubstituteCustomization { ConfigureMembers = true },
              new DefaultCustomization(),
              new SupportMutableValueTypesCustomization(),
              new FixtureCustomization(t))
    { }
}

public class FixtureCustomization : ICustomization
{
    private readonly Type _t;
    public FixtureCustomization(Type t)
    {
        _t = t;
    }

    public void Customize(IFixture fixture)
    {
        if (_t is null) return;

        var autofixtures = _t.GetMethods(System.Reflection.BindingFlags.Public | System.Reflection.BindingFlags.Static);
        var methodInfos = autofixtures.Where(x => x.ReturnType.Equals(typeof(Action<IFixture>))).ToList();
        foreach (var method in methodInfos)
        {
            if (method is not null)
            {
                var r = (Action<IFixture>)method.Invoke(null, null);
                r.Invoke(fixture);
            }
        }
    }
}

public class DefaultCustomization : ICustomization
{
    public void Customize(IFixture fixture)
    {
        fixture.Customize<MockHttpMessageHandler>(b => b.FromFactory(() =>
         {
             return new MockHttpMessageHandler();
         }));

        fixture.Customize<HttpClient>(b => b.FromFactory(() =>
        {
            var handler = fixture.Create<MockHttpMessageHandler>();
            return new HttpClient(handler);
        }));

        fixture.Customize<IServiceCollection>(b => b.FromFactory(() =>
        {
            var services = new ServiceCollection();
            services.AddLogging();
            services.AddHttpClient();
            return services;
        }));
    }
}