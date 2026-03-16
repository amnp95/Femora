from abc import ABC, abstractmethod
from femora.components.Material.materialBase import MaterialManager

class Action(ABC):
    """
    Abstract base class for all actions in the DRM_GUI.

    This class serves as a blueprint for creating specific actions
    that can be converted into a TCL script representation.
    """

    @abstractmethod
    def to_tcl(self) -> str:
        """
        Convert the action to its TCL script representation.

        This method must be implemented by all subclasses to define
        how the action is represented in TCL script format.

        Returns:
            str: A string containing the TCL script representation of the action.
        """
        raise NotImplementedError("Subclasses must implement the 'to_tcl' method.")



class wipe(Action):
    """
    Action to wipe the current mesh.

    This action clears the current mesh and prepares the system for a new mesh.
    """

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(wipe, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def to_tcl(self) -> str:
        return "wipe"
    

class wipeAnalysis(Action):
    """
    Action to wipe the current analysis.

    This action clears the current analysis and prepares the system for a new analysis.
    """

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(wipeAnalysis, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def to_tcl(self) -> str:
        return "wipeAnalysis"
    

class updateMaterialStageToElastic(Action):
    """
    Action to update all materials to elastic stage.
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(updateMaterialStageToElastic, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def to_tcl(self) -> str:
        cmd = ""
        for mat in MaterialManager().get_all_materials().values():
            tmp = mat.updateMaterialStage("Elastic")
            if tmp != "":
                cmd += tmp + "\n"
        return cmd
    
class updateMaterialStageToPlastic(Action):
        """
        Action to update all materials to plastic stage.
        """
        _instance = None

        def __new__(cls, *args, **kwargs):
            if cls._instance is None:
                cls._instance = super(updateMaterialStageToPlastic, cls).__new__(cls, *args, **kwargs)
            return cls._instance

        def to_tcl(self) -> str:
            cmd = ""
            for mat in MaterialManager().get_all_materials().values():
                tmp = mat.updateMaterialStage("Plastic")
                if tmp != "":
                    cmd += tmp + "\n"
            return cmd
        
class reset(Action):
    """
    Action to reset the mesh to its initial state.
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(reset, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def to_tcl(self) -> str:
        return "reset"
    
class loadConst(Action):
    """
    Action to load a constant.
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(loadConst, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def to_tcl(self) -> str:
        return "loadConst"


class removeLoadPatterns(Action):
    """Action to remove all load patterns."""

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(removeLoadPatterns, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def to_tcl(self) -> str:
        # Emit OpenSees commands to remove every currently-defined pattern.
        # Doing this via a stage action keeps staged workflows consistent
        # between TCL export and the solver backend.
        try:
            from femora.components.Pattern.patternBase import Pattern
        except Exception:
            return ""

        tags = sorted(int(tag) for tag in Pattern.get_all_patterns().keys())
        if not tags:
            return ""
        return "\n".join(f"remove loadPattern {tag}" for tag in tags)


class removeRecorders(Action):
    """Action to remove all recorders."""

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(removeRecorders, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def to_tcl(self) -> str:
        return "remove recorders"
    

class seTime(Action):
    """
    Action to set the time.
    """

    def __init__(self, pseudo_time: float):
        """
        Initialize the seTime action with a pseudo time.

        Args:
            pseudo_time (float): The pseudo time to set.
        """
        self.pseudo_time = pseudo_time

    def to_tcl(self) -> str:
        return f"setTime {self.pseudo_time}"
    

class exit(Action):
    """
    Action to exit the application.
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(exit, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def to_tcl(self) -> str:
        return "exit"
    

class tcl(Action):
    """
    Action to execute a TCL command.

    This action allows the execution of a TCL command directly.
    """
    def __init__(self, command: str):
        """
        Initialize the tcl action with a command.

        Args:
            command (str): The TCL command to execute.
        """
        self.command = command

    def to_tcl(self) -> str:
        return self.command


class ActionManager:
    """
    A container for all action classes in femora.
    
    This class provides direct access to the action classes rather than instances,
    allowing users to create instances when needed by calling the class.
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ActionManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        
        # Store the action classes directly
        self.wipe = wipe
        self.wipeAnalysis = wipeAnalysis
        self.updateMaterialStageToElastic = updateMaterialStageToElastic
        self.updateMaterialStageToPlastic = updateMaterialStageToPlastic
        self.reset = reset
        self.loadConst = loadConst
        self.removeLoadPatterns = removeLoadPatterns
        self.removeRecorders = removeRecorders
        self.exit = exit
        self.seTime = seTime
        self.tcl = tcl

    
    
    
    @classmethod
    def get_instance(cls):
        """
        Get the singleton instance of ActionManager.
        
        Returns:
            ActionManager: The singleton instance
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance


