"""
BaseHelperFormatter - abstract base for language-specific helper file formatters.

Helper formatters produce the companion files a solution needs —
TreeNode / ListNode class modules — derived from the test bundle's
method signature: if a param or return type mentions a node structure,
the matching module is placed next to the solution file.

Which structures require a helper file is determined here. Per-language
filename and file content are defined in each subclass.
"""

from abc import ABC, abstractmethod
from typing import Dict, List

from bytedojo.core.models.data_structure import DataStructure
from bytedojo.core.models.signature import Signature
from bytedojo.core.models.test_bundle import TestSignature

#: Structures that need a companion class module alongside the solution.
_HELPER_STRUCTURES = (DataStructure.BINARY_TREE, DataStructure.LINKED_LIST)


def node_structures(signature: TestSignature) -> List[DataStructure]:
    """Node structures referenced anywhere in a method signature, in order."""
    found: List[DataStructure] = []

    def visit(sig: Signature) -> None:
        for part in (sig.base, sig.element):
            if (
                isinstance(part, DataStructure)
                and part in _HELPER_STRUCTURES
                and part not in found
            ):
                found.append(part)

    for param in signature.params:
        visit(param.type)
    visit(signature.returns)
    return found


class BaseHelperFormatter(ABC):
    """Abstract base for language-specific helper file formatters."""

    @abstractmethod
    def filename(self, ds: DataStructure) -> str:
        """Return the output filename for a given data structure."""
        ...

    @abstractmethod
    def build_file(self, ds: DataStructure) -> str:
        """Return the complete file content for a given data structure."""
        ...

    def files_for(self, signature: TestSignature) -> Dict[str, str]:
        """{filename: content} for every node structure the signature needs."""
        return {
            self.filename(ds): self.build_file(ds) for ds in node_structures(signature)
        }

    def companion_imports(self, signature: TestSignature) -> List[str]:
        """Import/include lines for companion files needed by this signature.

        Default: none. Override in languages where companion files must be
        explicitly referenced in the solution (Python, C++).
        """
        return []
