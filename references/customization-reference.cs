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