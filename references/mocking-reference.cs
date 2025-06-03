public class MockHttpMessageHandler : HttpMessageHandler
{
    public Func<HttpResponseMessage> MockedResponse { get; set; }
    public HttpRequestMessage OriginalRequest { get; private set; }

    public MockHttpMessageHandler()
    { }

    protected override Task<HttpResponseMessage> SendAsync(HttpRequestMessage request, CancellationToken cancellationToken)
    {
        if (MockedResponse == null)
        {
            throw new InvalidOperationException("MockedResponse is not set");
        }
        OriginalRequest = request;
        return Task.FromResult(MockedResponse.Invoke());
    }

    protected override HttpResponseMessage Send(HttpRequestMessage request, CancellationToken cancellationToken)
    {
        if (MockedResponse == null)
        {
            throw new InvalidOperationException("MockedResponse is not set");
        }
        OriginalRequest = request;
        return MockedResponse.Invoke();
    }
}