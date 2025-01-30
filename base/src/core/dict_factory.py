# /*************************************************************************
# *
# * Copyright 2025 highstreet technologies and others
# *
# * Licensed under the Apache License, Version 2.0 (the "License");
# * you may not use this file except in compliance with the License.
# * You may obtain a copy of the License at
# *
# *     http://www.apache.org/licenses/LICENSE-2.0
# *
# * Unless required by applicable law or agreed to in writing, software
# * distributed under the License is distributed on an "AS IS" BASIS,
# * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# * See the License for the specific language governing permissions and
# * limitations under the License.
# ***************************************************************************/

class DictFactory:
    """Factory for creating dictionary templates based on a type."""
    templates = {}

    def __init__(self) -> None:
        raise Exception("DictFactory should not be instantiated")

    @staticmethod
    def add_template(template_type: str, template_class) -> None:
        existing_template_class = DictFactory.templates.get(template_type)
        if existing_template_class:
            return

        DictFactory.templates[template_type] = template_class

    @staticmethod
    def get_template(template_type: str):
        """Returns an instance of a template based on the template type."""

        template_class = DictFactory.templates.get(template_type)
        if not template_class:
            raise ValueError("Unknown template type")
        return template_class()


class BaseTemplate:
    """Base class for dictionary templates, providing shared functionality."""

    def __init__(self):
        self.data = self.create_dict()

    def create_dict(self):
        """Subclasses must implement this method to define their dictionary template."""
        raise NotImplementedError("Subclasses must implement create_dict method.")

    def update_key(self, path, value, append_to_list=False):
        """
        Updates or appends the value of a key in the dictionary, supporting paths through nested dictionaries and lists.
        If the final key points to a list and append_to_list is True, the value is appended to the list instead of replacing it.
        The path to the key is provided as a list of keys/indexes.
        """
        current_level = self.data
        for i, key in enumerate(path[:-1]):  # Navigate through all but the last key/index
            if isinstance(current_level, list):
                # Ensure the key is an integer index for lists
                if not isinstance(key, int):
                    raise KeyError(f"Expected an integer index for list, got {type(key).__name__} at path segment {key}")
                if key >= len(current_level):
                    raise IndexError(f"Index {key} out of range for list at path segment {path[:i+1]}")
            elif not isinstance(current_level, dict) or key not in current_level:
                raise KeyError(f"Key '{key}' not found at path segment {path[:i+1]}")
            current_level = current_level[key]

        # For the last key/index in the path, check if it's meant to append to a list
        if append_to_list and isinstance(current_level, list):
            current_level.append(value)
        elif append_to_list and path[-1] in current_level and isinstance(current_level[path[-1]], list):
            current_level[path[-1]].append(value)
        else:
            current_level[path[-1]] = value

    def delete_key(self, path):
        """
        Removes a key from the dictionary, supporting paths through nested dictionaries and lists.
        If the final key points to a list, the corresponding item is removed from the list.
        The path to the key is provided as a list of keys/indexes.
        """
        current_level = self.data
        for i, key in enumerate(path[:-1]):
            if isinstance(current_level, list):
                if not isinstance(key, int) or key >= len(current_level):
                    raise IndexError(f"Index {key} out of range or invalid for list at path segment {path[:i+1]}")
            elif not isinstance(current_level, dict) or key not in current_level:
                raise KeyError(f"Key '{key}' not found at path segment {path[:i+1]}")
            current_level = current_level[key]

        # For the last key/index in the path, remove the key/item
        if isinstance(current_level, list) and isinstance(path[-1], int):
            if path[-1] >= len(current_level):
                raise IndexError(f"Index {path[-1]} out of range for list at final path segment")
            current_level.pop(path[-1])
        elif isinstance(current_level, dict):
            if path[-1] in current_level:
                del current_level[path[-1]]
            else:
                raise KeyError(f"Key '{path[-1]}' not found for deletion.")
        else:
            raise TypeError("Cannot delete from a non-dictionary/non-list object.")
