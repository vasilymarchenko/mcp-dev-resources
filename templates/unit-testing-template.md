> **TL;DR for Copilot**
> * Use xUnit + FluentAssertions + AutoFixture + NSubstitute
> * Test name: `UnitOfWork_StateUnderTest_ExpectedOutcome`
> * Cover all public methods
> * Provide guard‑tests via GuardClauseAssertion
> * Inject dependencies with `DefaultAutoDataAttribute`

# Unit Test Generation Guidelines

## Testing Frameworks and Tools

- **xUnit:** Utilize xUnit as the primary testing framework.
- **FluentAssertions:** Use FluentAssertions for expressive assertions.
- **AutoFixture:** Employ AutoFixture for automatic generation of test data.
- **NSubstitute** Use NSubstitute for mocking.

## Naming Conventions

- **Method Naming:** Adopt the "UnitOfWork_StateUnderTest_ExpectedBehavior" naming convention for test methods to clearly convey their purpose.

## Null Guard Tests

Implement null guard tests for constructors and public methods as follows:

```csharp
{{ example_content('nullguards-examples.cs') }}
```

## Dependency Injection with AutoFixture

- **Injection with Attributes**: Use AutoFixture to inject dependencies with the `[Theory, DefaultAutoData]` attribute:

```csharp
public class DefaultAutoDataAttribute : AutoDataAttribute
{
    public DefaultAutoDataAttribute(Type? t = null)
        : base(() => new Fixture().Customize(new DefaultCompositeCustomization(t)))
    {
    }
}
```
- **Customization**: Apply AutoFixture customizations `Action<IFixture> AutoSetup()` in the test class when necessary. For example:
```csharp
{{ example_content('autsetup-examples.cs') }}
```

## Example Test Classes

Refer to the following test classes for examples:

```csharp
{{ example_content('testing-examples.cs') }}
```

These classes demonstrate the application of the aforementioned frameworks, tools, and conventions in real-world scenarios.

## Code reference

Rely on the already existing customizations. Do not reimplement them. The code below is just for illustration.

```csharp
{{ reference_content('customization-reference.cs') }}
```

Use `MockHttpMessageHandler` to mock HTTP requests. 
DO NOT reimplement `MockHttpMessageHandler` — it is already available as a shared component via NuGet.
The code below is provided only to illustrate its functionality.

```csharp
{{ reference_content('mocking-reference.cs') }}
```
