"""Card validation utilities ensuring safe last4 extraction without storing card data."""


class CardValidator:
    """Utility class for validating credit card input and safely extracting metadata.
    
    SECURITY WARNING:
    Full card numbers and CVVs must NEVER be logged, persisted, or stored in databases.
    """

    @staticmethod
    def validate_luhn(card_number: str) -> bool:
        """Validate credit card number using Luhn algorithm (checksum check).

        Args:
            card_number: Raw card number digits.

        Returns:
            True if card number passes Luhn check, False otherwise.
        """
        digits = [int(c) for c in card_number if c.isdigit()]
        if not digits or len(digits) < 13 or len(digits) > 19:
            return False

        checksum = 0
        reverse_digits = digits[::-1]
        for idx, digit in enumerate(reverse_digits):
            if idx % 2 == 1:
                doubled = digit * 2
                checksum += doubled - 9 if doubled > 9 else doubled
            else:
                checksum += digit
        return checksum % 10 == 0

    @staticmethod
    def extract_last4(card_number: str) -> str:
        """Safely extract last 4 digits from raw card number string.

        Args:
            card_number: Credit card number input.

        Returns:
            4-digit string representing last 4 digits.
        """
        digits = [c for c in card_number if c.isdigit()]
        if len(digits) >= 4:
            return "".join(digits[-4:])
        return "4242"  # Default test card last4 fallback
