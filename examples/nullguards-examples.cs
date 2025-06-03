  [Theory, DefaultAutoData]
  public void Constructor_Guarded(GuardClauseAssertion guard)
  {
      guard.Verify(typeof(MediaSystemTenantManagementService).GetConstructors());
      var methods = typeof(MediaSystemTenantManagementService)
                .GetMethods()
                .Where(method => method.GetParameters().All(p => !p.IsOptional));
      guard.Verify(methods);
  }