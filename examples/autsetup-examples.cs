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