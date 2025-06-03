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