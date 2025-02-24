import random
from typing import Any, Callable, Generic, Iterable, Iterator, Mapping, Optional, TypeVar, overload
import warnings
from umini.data.tree.base.vertex import Vertex, VertexComparable, VertexComputable, VertexOp

T = TypeVar('T', bound=VertexComparable)
T_co = TypeVar('T_co', bound=VertexComputable, covariant=True)

class _TreapVertex(Vertex[T_co]):
    """
    Internal class for treap vertex.
    Randomly generates priority for each vertex.
    
    Attributes:
        _priority: priority of the vertex.
        _size: size of the vertex.
        _left: left child of the vertex.
        _right: right child of the vertex.
        __lazy_calls: lazy calls of the vertex.
        __func_calls: function calls of the vertex.
    """
    def __init__(
        self, 
        value: T_co, 
        value_func: Optional[Callable[[T_co, T_co], T_co]] = None,
        *args: list[str],
        **kwargs: dict[str, T_co]
    ):
        """
        Initialize the vertex.

        Args:
            value: value of the vertex.
            value_func: function to compute the value of the vertex.
            args: positional arguments to pass to the vertex.
            kwargs: keyword arguments to pass to the vertex.
        """
        super().__init__(value)
        self._priority: int = random.randint(0, 1000000)
        self._size: int = 1
        self._left: Optional['_TreapVertex[T_co]'] = None
        self._right: Optional['_TreapVertex[T_co]'] = None
        self.__lazy_calls: dict[str, VertexOp] = {}
        self.__func_calls: dict[str, VertexOp] = {}

        self.__func_calls['value'] = value_func
        self.args = args
        self.kwargs = kwargs

    def __init_subclass__(cls, **kwargs: Any) -> None:
        for field, type in cls.__annotations__.items():
            if not issubclass(type, T_co):
                warnings.warn(f'{field} cannot be used as a computable field')

    @property
    def left(self) -> Optional['_TreapVertex[T_co]']:
        return self._left
    
    @left.setter
    def left(self, value: Optional['_TreapVertex[T_co]']) -> None:
        self._left = value

    @property
    def right(self) -> Optional['_TreapVertex[T_co]']:
        return self._right
    
    @right.setter
    def right(self, value: Optional['_TreapVertex[T_co]']) -> None:
        self._right = value
    

    @overload
    @classmethod
    def computable(
        cls,
        self: '_TreapVertex[T_co]',
        func: Callable[[T_co, T_co], T_co],
        field: str,
        reverse_func: Callable[[T_co, T_co], T_co],
        on_range: bool = True
    ) -> Callable[['_TreapVertex[T_co]'], Optional['_TreapVertex[T_co]']]: ...

    @overload
    @classmethod
    def computable(
        cls,
        self: '_TreapVertex[T_co]',
        func: Callable[[T_co, Optional[T_co]], Optional[T_co]],
        field: str,
        on_range: bool = False,
    ) -> Callable[['_TreapVertex[T_co]'], Optional['_TreapVertex[T_co]']]: ...

    @classmethod
    def computable(
        cls,
        self: '_TreapVertex[T_co]',
        field: str,
        reverse_func: Optional[Callable[[T_co, T_co], T_co]] = None,
        on_range: Optional[bool] = False,
    ) -> VertexOp:
        """
        Decorator to make a field computable.

        Args:
            field: name of the field.
            on_range: whether the field function is a range update.
            reverse_func: reverse function for range update. Required if on_range is True.
        
        Returns:
            VertexOp: function to compute the field.
        
        Raises:
            ValueError: if the field is not a class attribute or not a computable field.
            ValueError: if on_range is True but reverse_func is not provided.
        """
        def decorator(
            func: Callable[[T_co, Optional[T_co]], Optional[T_co]],
        ) -> VertexOp:
            if field not in cls.__annotations__:
                raise ValueError(f'{field} is not a class attribute')
            if not issubclass(cls.__annotations__[field], T_co):
                raise ValueError(f'{field} is not a computable field')
            if on_range:
                if reverse_func is None:
                    raise ValueError('reverse_func is required for on_range computable fields')
                def wrapper(self: _TreapVertex[T_co], push_value: T_co) -> Optional[_TreapVertex[T_co]]:
                    if self:
                        self.__setattr__(field, reverse_func(self.__getattr__(field), push_value))
                    if self._left:
                        self._left.__setattr__(field, func(self._left.__getattr__(field), push_value))
                    if self._right:
                        self._right.__setattr__(field, func(self._right.__getattr__(field), push_value))
                    return self
                self.__lazy_calls[field] = wrapper
            else:
                def wrapper(self: _TreapVertex[T_co]) -> Optional[_TreapVertex[T_co]]:
                    if self:
                        self.__setattr__(
                            field,
                            func(
                                self._left.__getattr__(field) or T_co(), 
                                self._right.__getattr__(field) or T_co()
                            )
                        )
                    return self
                self.__func_calls[field] = wrapper
            return wrapper
        return decorator
    
    def push(self, **kwargs: dict[str, T_co]) -> None:
        """
        Push the vertex.

        Args:
            kwargs: keyword arguments to push.
        """
        if self:
            for attr, value in kwargs.items():
                if self.__lazy_calls.get(attr, None):
                    self.__lazy_calls[attr](self, value)

    def update(self, *args: list[str]) -> None:
        """
        Update the vertex.

        Args:
            args: list of attributes to update.
        """
        if self:
            self._size = len(self._left) + len(self._right) + 1
            for attr in args:
                if self.__func_calls.get(attr, None):
                    self.__func_calls[attr](self)
            else:
                for attr in self.__func_calls:
                    self.__func_calls[attr](self)

    def split(
        self,
        key: int, 
        add: int = 0, 
        *args: list[str],
        **kwargs: dict[str, T_co]
    ) -> tuple['_TreapVertex[T_co]', '_TreapVertex[T_co]']:
        if not self:
            return self, self
        self.push(**kwargs)
        cur_key = len(self.left) + add
        if cur_key <= key:
            left, right = self.left.split(key, add, **kwargs)
            right = self
        else:
            left, right = self.right.split(key, add + len(self.left) + 1, **kwargs)
            left = self
        self.update(*args)
        return left, right
    
    def merge(
        self, 
        l: '_TreapVertex[T_co]', 
        r: '_TreapVertex[T_co]', 
        *args: list[str],
        **kwargs: dict[str, T_co]
    ) -> '_TreapVertex[T_co]':
        l.push(**kwargs)
        r.push(**kwargs)
        if not l or not r:
            return l or r
        if l._priority > r._priority:
            l.right = self.merge(l.right, r, *args, **kwargs)
            return l
        r.left = self.merge(l, r.left, *args, **kwargs)
        self.update(*args)
        return r
        
    def __len__(self) -> int:
        if self:
            return self._size
        return 0
    
    def __bool__(self) -> bool:
        return self._size > 0 and self.value is not None

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(
        value={self.value}, 
        priority={self._priority}, 
        size={self._size}, 
        left={self._left}, 
        right={self._right})'
    
    def __str__(self) -> str:
        return f'{self.__class__.__name__}(
        value={self.value}, 
        priority={self._priority}, 
        size={self._size}, 
        left={self._left}, 
        right={self._right})'

VT = TypeVar('VT', bound=_TreapVertex)

class ImplicitTreap(Generic[VT, T_co]):
    def __init__(self, root: Optional[VT] = None):
        self._tree: Optional[VT] = root

    def range(self, start: int, end: int) -> Iterable[T_co]:
        ...

    # Set
    @overload   
    def __setitem__(self, key: int, value: T_co) -> None: ...

    @overload
    def __setitem__(self, key: slice, value: Iterable[T_co]) -> None: ...

    def __setitem__(self, key: int | slice, value: T_co | Iterable[T_co]) -> None:
        ...
    # Get
    @overload
    def __getitem__(self, key: int) -> T_co: ...

    @overload
    def __getitem__(self, key: slice) -> Iterable[T_co]: ...

    def __getitem__(self, key: int | slice) -> T_co | Iterable[T_co]:
        ...

    # Delete
    @overload
    def __delitem__(self, key: int) -> None: ...

    @overload
    def __delitem__(self, key: slice) -> None: ...

    def __delitem__(self, key: int | slice) -> None:
        ...
    
    # Max
    @overload
    def __max__(self) -> T_co: ...

    @overload
    def __max__(self, key: Callable[[T_co], Any]) -> T_co: ...

    def __max__(self, key: Optional[Callable[[T_co], Any]] = None) -> T_co:
        ...
    
    # Min
    @overload
    def __min__(self) -> T_co: ...

    @overload
    def __min__(self, key: Callable[[T_co], Any]) -> T_co: ...

    def __min__(self, key: Optional[Callable[[T_co], Any]] = None) -> T_co:
        ...
    
    # Length

    def __len__(self) -> int:
        return len(self._tree)
    
    def __bool__(self) -> bool:
        return self._tree is not None
