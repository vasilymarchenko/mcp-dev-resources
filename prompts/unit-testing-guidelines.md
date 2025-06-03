# Unit Testing Guidelines

> **TL;DR for Copilot**
> * Use xUnit + FluentAssertions + AutoFixture + NSubstitute
> * Test name: `UnitOfWork_StateUnderTest_ExpectedOutcome`
> * Cover all public methods
> * Provide guard‑tests via GuardClauseAssertion
> * Inject dependencies with `DefaultAutoDataAttribute`

# Unit Test Generation Guidelines

## Testing Frameworks and Tools

- **xUnit:** Utilize xUnit as the primary testing framework.
- **Shouldly:** Use Shouldly for expressive assertions.
- **AutoFixture:** Employ AutoFixture for automatic generation of test data.
- **NSubstitute** Use NSubstitute for mocking.

## Naming Conventions

- **Method Naming:** Adopt the "UnitOfWork_StateUnderTest_ExpectedBehavior" naming convention for test methods to clearly convey their purpose.

## Custom AutoFixture Attributes (Quick Reference)

- `DefaultAutoDataAttribute`: Provides a pre-customized fixture for most tests. Applies core customizations and supports type-specific fixture setup via AutoSetup().

- `AutoNSubPropertyDataAttribute`: Like MemberData, but with automatic fixture generation and support for NSubstitute integration.

- `DefaultInlineAutoDataAttribute`: For inline parameterized data with the same fixture benefits.

### Implementation Reference for Custom Attributes and Customizations

> **Note for Copilot:**  
> The following code snippets illustrate the implementation and intended usage of custom test attributes and fixture customizations that are distributed via an internal NuGet package. Do **not** copy these snippets directly into test classes. Instead, always use the provided attributes (`DefaultAutoDataAttribute`, etc.) in your test code **in place of the default xUnit or AutoFixture attributes**. The code is provided here for understanding and context, not for duplication.

```csharp
    public class DefaultAutoDataAttribute : AutoDataAttribute
    {
        public DefaultAutoDataAttribute(Type? t = null)
            : base(() => new Fixture().Customize(new DefaultCompositeCustomization(t)))
        {
        }
    }

    public class AutoNSubPropertyDataAttribute : MemberAutoDataAttribute
    {
        public AutoNSubPropertyDataAttribute(string propertyName, params object[] values)
            : base(new DefaultAutoDataAttribute(null), propertyName, values)
        {
        }

        public AutoNSubPropertyDataAttribute(Type? t, string propertyName, params object[] values)
            : base(new DefaultAutoDataAttribute(t), propertyName, values)
        {
        }
    }

    public class DefaultInlineAutoDataAttribute : InlineAutoDataAttribute
    {
        public DefaultInlineAutoDataAttribute(params object[] values)
            : base(new DefaultAutoDataAttribute(null), values)
        {
        }

        public DefaultInlineAutoDataAttribute(Type? t, params object[] values)
            : base(new DefaultAutoDataAttribute(t), values)
        {
        }
    }
```

## Null Guard Tests

Implement null guard tests for constructors and public methods as follows:
```csharp
  [Theory, DefaultAutoData]
  public void Constructor_Guarded(GuardClauseAssertion guard)
  {
      guard.Verify(typeof(MediaSystemTenantManagementService).GetConstructors());
      var methods = typeof(MediaSystemTenantManagementService)
                .GetMethods()
                .Where(method => method.GetParameters().All(p => !p.IsOptional));
      guard.Verify(methods);
  }
```
## Dependency Injection and Fixture Customization

- Always inject dependencies with `[Theory, DefaultAutoData]` for DRY, deterministic setup.
    
- If extra setup is needed for a type, add a public static `Action<IFixture> AutoSetup()` method in the test class. The custom fixture will invoke this automatically.

```csharp
[Theory, DefaultAutoData(typeof(MyServiceTests))]
public void DoSomething_Works(MyService sut, AnotherService service)
{
    // test
}
public static Action<IFixture> AutoSetup()
{
    return fixture =>
    {
        fixture.Customize<AnotherService>(c => 
            // Custom fixture configuration here
        );
    };
}
```

## Existing mocks and customizations

These mocks and customizations are available out of the box. Yiu don't need to imblement it by yourself, just use them

### MockHttpMessageHandler

Use `MockHttpMessageHandler` for testing code that interacts with HttpClient and requires low-level HTTP simulation (rather than just interface substitution).

```csharp
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
```

### Rely on the already exist customizatios:
```csharp

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
```

## Example Test Classes

Refer to the following test classes for examples:

- `tests/Sitecore.MMS.Management.Core.UnitTests/Services/Azure/AzureStorageManagementServiceTests.cs`
- `tests/Sitecore.MMS.Management.Core.UnitTests/Services/CHCreateOperationsTests.cs`
- `tests/Sitecore.MMS.Management.Core.UnitTests/Services/TokenProviderTests.cs`

These classes demonstrate the application of the aforementioned frameworks, tools, and conventions in real-world scenarios.

## Anti-Patterns to Avoid

- ❌ Hand-crafted test data (prefer AutoFixture)
    
- ❌ Using `[Fact]` when parameterization is needed
    
- ❌ Asserting against implementation details (test only observable behavior)
    
- ❌ Duplicating fixture setup in multiple tests (prefer customizations)

- ❌ Avoid testing of trivial pass-throughs (e.g., single-line property getters/setters without logic).
    
