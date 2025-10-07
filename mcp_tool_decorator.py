import azure.functions as func
import json
import inspect
from typing import get_origin, get_args, Annotated, Tuple, Any, Callable, Dict


class MCPToolContext(Dict[str, Any]):
    pass


class ToolProperty:
    def __init__(self, property_name: str, property_type: str, description: str):
        self.propertyName = property_name
        self.propertyType = property_type
        self.description = description

    def to_dict(self):
        return {
            "propertyName": self.propertyName,
            "propertyType": self.propertyType,
            "description": self.description,
        }


def _extract_type_and_description(param_name: str, type_hint: Any) -> Tuple[Any, str]:
    """
    Extract the actual type and description from a type hint, handling Annotated types.
    
    Args:
        param_name: The parameter name
        type_hint: The type hint (could be Annotated or regular type)
    
    Returns:
        tuple: (actual_type, description)
    """
    # Check if it's an Annotated type
    if get_origin(type_hint) is Annotated:
        args = get_args(type_hint)
        actual_type = args[0]  # First argument is the actual type
        # Look for string descriptions in the annotations
        param_description = f"The {param_name} parameter."  # Default description
        for annotation in args[1:]:
            if isinstance(annotation, str):
                param_description = annotation
                break
        return actual_type, param_description
    else:
        # Regular type hint
        return type_hint, f"The {param_name} parameter."


def mcp_tool(app: func.FunctionApp) -> Callable[[Callable], Callable]:
    """
    Decorator that automaticallycreates an MCP tool trigger from a function.
    
    Args:
        app: The Azure Functions app instance to register the function with
    
    Infers:
    - Tool name from function name
    - Description from function docstring
    - Argument names and types from function signature
    """
    def decorator(target_func: Callable) -> Callable:
        # IMPORTANT: Extract all function metadata BEFORE applying Azure Functions decorator
        # because the Azure Functions decorator will wrap the function and change its signature
        
        # Get function signature and type hints from the original function
        sig = inspect.signature(target_func)
        
        # Extract tool name from function name
        tool_name = target_func.__name__
        
        # Extract description from docstring
        func_description = ""
        if target_func.__doc__:
            # Take the first line of the docstring as description
            func_description = target_func.__doc__.strip().split('\n')[0]
        
        # Map Python types to MCP property types
        # TODO: Handle more complex cases if needed.
        type_mapping: Dict[Any, str] = {
            int: "integer",
            str: "string",
            float: "number",
            bool: "boolean",
        }
        
        # Create tool properties from function parameters
        tool_properties = []
        for param_name, param in sig.parameters.items():
            # Use the raw annotation from the parameter, not from get_type_hints()
            # get_type_hints() resolves Annotated[type, desc] to just type, losing the description
            param_type_hint = param.annotation if param.annotation != inspect.Parameter.empty else str
            
            # Extract actual type and description (handles Annotated types)
            actual_type, param_description = _extract_type_and_description(param_name, param_type_hint)
            
            # Skip MCPToolContext parameters - they should not be included in tool properties
            if actual_type is MCPToolContext:
                continue
            
            # Map the actual type to MCP property type
            property_type = type_mapping.get(actual_type, "string")
            
            tool_properties.append(ToolProperty(param_name, property_type, param_description))
        
        # Convert tool properties to JSON
        tool_properties_json = json.dumps([prop.to_dict() for prop in tool_properties])
        
        # Create the wrapper function that matches the expected signature
        def wrapper(context: str) -> str:
            try:
                content = json.loads(context)
                if "arguments" not in content:
                    return "Error: Missing 'arguments' field in context JSON"
                
                arguments = content["arguments"]
                
                # Extract arguments and call the original function
                kwargs = {}
                for param_name, param in sig.parameters.items():
                    # Get the actual type for this parameter
                    param_type_hint = param.annotation if param.annotation != inspect.Parameter.empty else str
                    actual_type, _ = _extract_type_and_description(param_name, param_type_hint)
                    
                    # If parameter is MCPToolContext, pass the deserialized context
                    if actual_type is MCPToolContext:
                        kwargs[param_name] = content
                    elif param_name in arguments:
                        kwargs[param_name] = arguments[param_name]
                    else:
                        return f"Error: Missing required parameter '{param_name}' for function '{tool_name}'"
                
                # Call the original function
                result = target_func(**kwargs)
                return str(result)
                
            except json.JSONDecodeError as e:
                return f"Error: Invalid JSON in context - {str(e)}"
            except TypeError as e:
                return f"Error: Invalid parameter types for function '{tool_name}' - {str(e)}"
            except Exception as e:
                return f"Error executing function '{tool_name}': {str(e)}"
        
        # Set the wrapper function name to match the original function
        wrapper.__name__ = target_func.__name__
        wrapper.__doc__ = target_func.__doc__
        
        # Apply the generic_trigger decorator
        decorated_func = app.generic_trigger(
            arg_name="context",
            type="mcpToolTrigger",
            toolName=tool_name,
            description=func_description,
            toolProperties=tool_properties_json,
        )(wrapper)
        
        return decorated_func
    
    return decorator


def get_mcp_tool(app: func.FunctionApp) -> Callable[[], Callable[[Callable], Callable]]:
    """
    Returns an MCP tool decorator for the given Azure Functions app.
    
    Args:
        app: The Azure Functions app instance to register functions with
    
    Returns:
        A decorator function that can be used to create MCP tools
    """
    def decorator_factory() -> Callable[[Callable], Callable]:
        return mcp_tool(app)
    
    return decorator_factory
