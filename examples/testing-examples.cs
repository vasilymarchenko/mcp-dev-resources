public class AzureStorageManagementServiceTests
{
    [Theory, DefaultAutoData]
    public void Ctor_Guarded(GuardClauseAssertion guard)
    {
        guard.Verify(typeof(AzureStorageManagementService).GetConstructors());
    }

    [Theory]
    [DefaultInlineAutoData((object)null, "weu", typeof(ArgumentNullException))]
    [DefaultInlineAutoData("", "weu", typeof(ArgumentException))]
    [DefaultInlineAutoData("tenantId", null, typeof(ArgumentNullException))]
    [DefaultInlineAutoData("tenantId", "", typeof(ArgumentException))]
    public async Task InitializeContainersAsync_Guarded(
        string tenantId,
        string location,
        Type expectedExceptionType,
        AzureStorageManagementService sut)
    {
        var action = async () => await sut.InitializeContainersAsync(tenantId, location);

        var ex = await action.Should().ThrowAsync<Exception>();
        ex.Which.Should().BeOfType(expectedExceptionType);
    }

    [Theory]
    [DefaultAutoData(typeof(AzureStorageManagementServiceTests))]
    public async Task InitializeContainersAsync_CreatesFilesStorageContainer(
        string tenantId,
        string location,
        BlobServiceClient blobServiceClient,
        BlobContainerClient client,
        [Frozen] BlobServiceClientFactory factory,
        AzureStorageManagementService sut)
    {
        blobServiceClient.GetBlobContainerClient($"{tenantId}-files").Returns(client);
        factory.GetTenantBlobServiceClient(Arg.Any<string>(), Arg.Any<string>()).Returns(blobServiceClient);
        await sut.InitializeContainersAsync(tenantId, location);
        await client.Received(1).CreateIfNotExistsAsync();
    }

    [Theory]
    [DefaultAutoData(typeof(AzureStorageManagementServiceTests))]
    public async Task InitializeContainersAsync_ThrowsIfContainerCannotBeCreated(
       string tenantId,
       string location,
       BlobServiceClient blobServiceClient,
       BlobContainerClient client,
       Response<BlobContainerInfo> response,
       [Frozen] BlobServiceClientFactory factory,
       AzureStorageManagementService sut)
    {
        client.CreateIfNotExistsAsync().Returns(response);
        blobServiceClient.GetBlobContainerClient($"{tenantId}-files").Returns(client);
        factory.GetTenantBlobServiceClient(Arg.Any<string>(), Arg.Any<string>()).Returns(blobServiceClient);
        var func = async () => await sut.InitializeContainersAsync(tenantId, location);
        await func.Should().ThrowAsync<RequestFailedException>();
    }

    [Theory]
    [DefaultInlineAutoData((object)null, "weu", typeof(ArgumentNullException))]
    [DefaultInlineAutoData("", "weu", typeof(ArgumentException))]
    [DefaultInlineAutoData("tenantId", null, typeof(ArgumentNullException))]
    [DefaultInlineAutoData("tenantId", "", typeof(ArgumentException))]
    public async Task RemoveResourcesAsync_Guarded(
        string tenantId,
        string location,
        Type expectedExceptionType,
        AzureStorageManagementService sut)
    {
        var action = async () => await sut.RemoveResourcesAsync(tenantId, location);

        var ex = await action.Should().ThrowAsync<Exception>();
        ex.Which.Should().BeOfType(expectedExceptionType);
    }

    [Theory]
    [DefaultAutoData(typeof(AzureStorageManagementServiceTests))]
    public async Task RemoveResourcesAsync_RemovesFilesStorageContainer(
        string tenantId,
        string location,
        BlobServiceClient blobServiceClient,
        BlobContainerClient client,
        [Frozen] BlobServiceClientFactory factory,
        AzureStorageManagementService sut)
    {
        blobServiceClient.GetBlobContainerClient($"{tenantId}-files").Returns(client);
        factory.GetTenantBlobServiceClient(Arg.Any<string>(), Arg.Any<string>()).Returns(blobServiceClient);
        await sut.RemoveResourcesAsync(tenantId, location);
        await client.Received(1).DeleteIfExistsAsync();
    }

    [Theory]
    [DefaultAutoData(typeof(AzureStorageManagementServiceTests))]
    public async Task RemoveResourcesAsync_ThrowsIfContainerCannotBeDeleted(
       string tenantId,
       string location,
       BlobServiceClient blobServiceClient,
       BlobContainerClient blobContainerClient,
       Response<bool> response,
       [Frozen] BlobServiceClientFactory factory,
       AzureStorageManagementService sut)
    {
        blobContainerClient.DeleteIfExistsAsync().Returns(Task.FromResult(response));
        blobServiceClient.GetBlobContainerClient($"{tenantId}-files").Returns(blobContainerClient);
        factory.GetTenantBlobServiceClient(Arg.Any<string>(), Arg.Any<string>()).Returns(blobServiceClient);
        var func = async () => await sut.RemoveResourcesAsync(tenantId, location);
        await func.Should().ThrowAsync<RequestFailedException>();
    }

    public static Action<IFixture> AutoSetup()
    {
        return fixture =>
        {
            fixture.Customize<BlobServiceClient>(b => b.FromFactory(() =>
            {
                return Substitute.For<BlobServiceClient>();
            }));

            fixture.Customize<BlobContainerClient>(b => b.FromFactory(() =>
            {
                return Substitute.For<BlobContainerClient>();
            }));

            var rawResponse = Substitute.For<AzureResponse>();
            rawResponse.Status.Returns(400);
            rawResponse.IsError.Returns(true);

            fixture.Customize<Response<BlobContainerInfo>>(b => b.FromFactory(() =>
            {
                var response = Substitute.For<Response<BlobContainerInfo>>();
                response.GetRawResponse().Returns(rawResponse);
                return response;
            }));

            fixture.Customize<Response<bool>>(b => b.FromFactory(() =>
            {
                var response = Substitute.For<Response<bool>>();
                response.GetRawResponse().Returns(rawResponse);
                return response;
            }));

            fixture.Customize<BlobServiceClientFactory>(b => b.FromFactory(() =>
            {
                var opt = Options.Create(new AzureConnectionStringsSettings
                {
                    Connections = new Dictionary<string, string>
                    {
                        { "weu", "DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;QueueEndpoint=http://127.0.0.1:10001/devstoreaccount1;\r\nTableEndpoint=http://127.0.0.1:10002/devstoreaccount1;" }
                    }
                });
                return Substitute.For<BlobServiceClientFactory>(opt);
            }));
        };
    }
}

    public class CHCreateOperationsTests
    {
        [Theory, DefaultAutoData]
        public void Null_Guarded(GuardClauseAssertion guard)
        {
            guard.Verify(typeof(OperationsFactoryCH));
        }

        [Theory, DefaultAutoData]
        public void CreateOperations_Should_Return_ExpectedOperations_When_OrganisationId_Is_Null(
            TenantInfo tenantInfo,
            OperationsFactoryCH operationsFactory)
        {
            // Arrange
            tenantInfo = CreateTenantInfoWithoutOrgID(tenantInfo);

            // Act
            var result = operationsFactory.CreateOperations(tenantInfo);

            // Assert
            result.Should().HaveCount(5);
            result.Should().ContainItemsAssignableTo<ICompensatableOperation>();
            result.Should().SatisfyRespectively(
                zero => zero.Should().BeOfType<ValidateDeactivationOperation>(),
                first => first.Should().BeOfType<AddToCdnOperation>(),
                second => second.Should().BeOfType<SetSettingsOperation>(),
                third => third.Should().BeOfType<AddToCdnUrlsOperation>(),
                fourth => fourth.Should().BeOfType<AddToTcsOperation>());
        }

        private static TenantInfo CreateTenantInfoWithoutOrgID(TenantInfo orig)
        {
            return new TenantInfo
            {
                TenantId = orig.TenantId,
                Location = orig.Location,
                OrganisationId = null,
                SubscriptionId = orig.SubscriptionId,
                Version = orig.Version,
                AzureConnectionString = orig.AzureConnectionString,
                UrlSignerKey = orig.UrlSignerKey,
                PortalApiEndpoint = orig.PortalApiEndpoint,
                DeliveryUrl = orig.DeliveryUrl,
                AdditionalListeningURLs = orig.AdditionalListeningURLs,
                RequestingSystem = orig.RequestingSystem
            };
        }

        [Theory, DefaultAutoData]
        public void CreateOperations_Should_Return_ExpectedOperations_When_OrganisationId_Is_Not_Null(
            TenantInfo tenantInfo,
            OperationsFactoryCH operationsFactory)
        {
            // Act
            var result = operationsFactory.CreateOperations(tenantInfo);

            // Assert
            result.Should().HaveCount(9);
            result.Should().ContainItemsAssignableTo<ICompensatableOperation>();
            result.Should().SatisfyRespectively(
                zero => zero.Should().BeOfType<ValidateDeactivationOperation>(),
                first => first.Should().BeOfType<AddToInventory>(),
                second => second.Should().BeOfType<AddClientOperation>(),
                third => third.Should().BeOfType<AddClientGrantsOperation>(),
                fourth => fourth.Should().BeOfType<AddToCdnOperation>(),
                fifth => fifth.Should().BeOfType<SetSettingsOperation>(),
                sixth => sixth.Should().BeOfType<AddToCdnUrlsOperation>(),
                seventh => seventh.Should().BeOfType<AddToTcsOperation>(),
                eighth => eighth.Should().BeOfType<ActivateInventory>());
        }
    }

    public class TokenProviderTests
    {
        [Theory, DefaultAutoData]
        public void Ctor_Guarded(GuardClauseAssertion assertion)
        {
            assertion.Verify(typeof(TokenProvider).GetConstructors());
        }

        [Theory]
        [DefaultAutoData(typeof(TokenProviderTests))]
        public async Task GetTokenAsync_GuardsAgainstNullTokenRequestModel(
            TokenProvider sut)
        {
            //As soon as `GuardClauseAssertion` does not work with async methods, we need this test instead:
            await Assert.ThrowsAsync<ArgumentNullException>(() => sut.GetTokenAsync(null));
        }

        [Theory]
        [DefaultAutoData(typeof(TokenProviderTests))]
        public async Task GetTokenAsync_ReturnsToken_WhenResponseSuccessful(
            AuthenticationToken expectedToken,
            TokenRequestModel tokenRequestModel,
            [Frozen] IHttpClientFactory httpClientFactory,
            [Frozen] MockHttpMessageHandler handler,
            TokenProvider sut)
        {
            // Arrange
            handler.MockedResponse = () => new HttpResponseMessage(HttpStatusCode.OK)
            {
                Content = new StringContent(JsonSerializer.Serialize(expectedToken))
            };

            httpClientFactory.CreateClient(nameof(TokenProvider))
                             .Returns(new HttpClient(handler));

            // Act
            var result = await sut.GetTokenAsync(tokenRequestModel);

            // Assert
            result.Should().Be(expectedToken.AccessToken);
        }

        [Theory]
        [DefaultAutoData(typeof(TokenProviderTests))]
        public async Task GetTokenAsync_ThrowsException_WhenResponseNotSuccessful(
            TokenRequestModel tokenRequestModel,
            [Frozen] IHttpClientFactory httpClientFactory,
            [Frozen] MockHttpMessageHandler handler,
            TokenProvider sut)
        {
            // Arrange
            handler.MockedResponse = () => new HttpResponseMessage(HttpStatusCode.BadRequest);
            httpClientFactory.CreateClient(nameof(TokenProvider))
                             .Returns(new HttpClient(handler));

            // Act
            Func<Task> act = async () => await sut.GetTokenAsync(tokenRequestModel);

            // Assert
            await act.Should().ThrowAsync<Exception>()
                     .WithMessage("*Status code: 400*");
        }

        [Theory]
        [DefaultAutoData(typeof(TokenProviderTests))]
        public async Task GetTokenAsync_ThrowsNullReferenceException_WhenTokenDataInvalid(
            TokenRequestModel tokenRequestModel,
            [Frozen] IHttpClientFactory httpClientFactory,
            [Frozen] MockHttpMessageHandler handler,
            TokenProvider sut)
        {
            // Arrange
            // Return a JSON payload with null AccessToken.
            handler.MockedResponse = () => new HttpResponseMessage(HttpStatusCode.OK)
            {
                Content = new StringContent(
                    JsonSerializer.Serialize(new AuthenticationToken { AccessToken = null, ExpiresIn = 3600 }))
            };

            httpClientFactory.CreateClient(nameof(TokenProvider))
                             .Returns(new HttpClient(handler));

            // Act
            Func<Task> act = async () => await sut.GetTokenAsync(tokenRequestModel);

            // Assert
            await act.Should().ThrowAsync<NullReferenceException>()
                     .WithMessage("The retrieved token from authority server is 'null'.");
        }

        public static Action<IFixture> AutoSetup()
        {
            return fixture =>
            {
                fixture.Customize<TokenRequestModel>(c => c
                    .FromFactory(() => new TokenRequestModel
                    {
                        Audience = "https://example.com",
                        Authority = "https://example.com",
                    })
                    .Without(x => x.Audience)
                    .Without(x => x.Authority));
            };
        }
    }