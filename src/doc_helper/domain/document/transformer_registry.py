"""Transformer registry for managing available transformers."""

from doc_helper.domain.document.transformer import ITransformer


class TransformerRegistry:
    """Registry for managing available transformers.

    The registry allows:
    - Registering transformers by name
    - Retrieving transformers by name
    - Listing all available transformers

    Example:
        registry = TransformerRegistry()
        registry.register(UppercaseTransformer())
        registry.register(LowercaseTransformer())

        transformer = registry.get("uppercase")
        result = transformer.transform("hello")  # "HELLO"
    """

    def __init__(self) -> None:
        """Initialize empty registry."""
        self._transformers: dict[str, ITransformer] = {}

    def register(self, transformer: ITransformer) -> None:
        """Register a transformer.

        Args:
            transformer: Transformer to register

        Raises:
            TypeError: If transformer is not ITransformer
            ValueError: If transformer name already registered
        """
        if not isinstance(transformer, ITransformer):
            raise TypeError("transformer must implement ITransformer")

        if transformer.name in self._transformers:
            raise ValueError(f"Transformer '{transformer.name}' already registered")

        self._transformers[transformer.name] = transformer

    def get(self, name: str) -> ITransformer:
        """Get transformer by name.

        Args:
            name: Transformer name

        Returns:
            Transformer instance

        Raises:
            KeyError: If transformer not found
        """
        if name not in self._transformers:
            raise KeyError(f"Transformer '{name}' not found")

        return self._transformers[name]

    def has(self, name: str) -> bool:
        """Check if transformer is registered.

        Args:
            name: Transformer name

        Returns:
            True if transformer exists
        """
        return name in self._transformers

    def list_names(self) -> list[str]:
        """Get list of all registered transformer names.

        Returns:
            List of transformer names
        """
        return list(self._transformers.keys())

    def get_all(self) -> dict[str, ITransformer]:
        """Get all registered transformers.

        Returns:
            Dict of transformer name -> transformer instance
        """
        return self._transformers.copy()
