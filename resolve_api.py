"""
DaVinci Resolve API connector module.

This module provides functions to connect to DaVinci Resolve's Python API
and interact with its various components, such as projects, timelines, media pools, and more.
"""

import sys
import os
import platform
import logging
from typing import Optional, Dict, List, Any, Union, Tuple

# Configure logging with a standard format including timestamp, logger name, level, and message
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("ResolveAPI")  # Logger instance for this module

class ResolveAPI:
    """Class to handle connection and interaction with DaVinci Resolve API."""
    
    def __init__(self):
        """
        Initialize the ResolveAPI class and establish a connection to DaVinci Resolve.
        Sets up internal references to Resolve objects (e.g., project manager, media pool).
        """
        self.resolve = None  # Main Resolve application object
        self.fusion = None  # Fusion object for compositing
        self.project_manager = None  # Project manager object
        self.current_project = None  # Current project object
        self.media_storage = None  # Media storage object
        self.media_pool = None  # Media pool object for the current project
        self._connect_to_resolve()  # Attempt to connect to Resolve on initialization

    def _find_scripting_module(self) -> Optional[str]:
        """
        Dynamically locate the DaVinciResolveScript module path based on the operating system.
        Checks for a custom path via environment variable, then falls back to default locations.
        
        Returns:
            Optional[str]: Path to the scripting module if found, None otherwise.
        """
        custom_path = os.environ.get("RESOLVE_SCRIPT_PATH")  # Check for user-defined path
        if custom_path and os.path.exists(custom_path):
            return custom_path
        # Default paths for Resolve scripting module by OS
        base_paths = {
            "Windows": os.path.join(os.environ.get("PROGRAMDATA", "C:\\ProgramData"), "Blackmagic Design", "DaVinci Resolve", "Support", "Developer", "Scripting", "Modules"),
            "Darwin": ["/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting/Modules",
                       os.path.join(os.path.expanduser("~"), "Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting/Modules")],
            "Linux": "/opt/resolve/Developer/Scripting/Modules"
        }
        system = platform.system()  # Get current OS
        paths = base_paths.get(system, []) if system != "Darwin" else base_paths["Darwin"]
        for path in ([paths] if isinstance(paths, str) else paths):  # Handle single path or list
            if os.path.exists(path) and path not in sys.path:
                sys.path.append(path)  # Add to Python path if not already present
                return path
        return None  # Return None if no valid path is found

    def _connect_to_resolve(self) -> None:
        """
        Establish a connection to DaVinci Resolve by importing its scripting module.
        Initializes core objects (e.g., project manager, media pool) if successful.
        """
        script_path = self._find_scripting_module()  # Find the scripting module path
        if not script_path:
            logger.error("No valid Resolve scripting module path found")
            return
        try:
            import DaVinciResolveScript as dvr_script  # Import the Resolve scripting API
            self.resolve = dvr_script.scriptapp("Resolve")  # Connect to Resolve app
            logger.info(f"Connected to Resolve using {script_path}")
        except ImportError:
            logger.error(f"Failed to import DaVinciResolveScript from {script_path}")
            self.resolve = None
        if self.resolve:  # If connection is successful, initialize other objects
            self.project_manager = self.resolve.GetProjectManager()
            self.current_project = self.project_manager.GetCurrentProject()
            self.media_storage = self.resolve.GetMediaStorage()
            self.fusion = self.resolve.Fusion()
            self.media_pool = self.current_project.GetMediaPool() if self.current_project else None

    def refresh(self) -> None:
        """
        Refresh all internal Resolve objects to ensure they reflect the current state.
        Useful if Resolve's state changes externally (e.g., project switch).
        """
        if not self.resolve:  # Reconnect if not already connected
            self._connect_to_resolve()
        if self.resolve:
            self.project_manager = self.resolve.GetProjectManager()  # Update project manager
            self.current_project = self.project_manager.GetCurrentProject()  # Update current project
            self.media_storage = self.resolve.GetMediaStorage()  # Update media storage
            self.fusion = self.resolve.Fusion()  # Update Fusion object
            self.media_pool = self.current_project.GetMediaPool() if self.current_project else None  # Update media pool
            logger.info("Refreshed Resolve API state")

    def is_connected(self) -> bool:
        """
        Check if the API is connected to DaVinci Resolve.
        
        Returns:
            bool: True if connected, False otherwise.
        """
        return self.resolve is not None

    def get_project_manager(self):
        """
        Get the project manager object.
        
        Returns:
            Any: ProjectManager object or None if not connected.
        """
        return self.project_manager

    def get_current_project(self):
        """
        Get the current project object, refreshing it from the project manager.
        
        Returns:
            Any: Current Project object or None if no project is open.
        """
        if self.project_manager:
            self.current_project = self.project_manager.GetCurrentProject()
        return self.current_project

    def get_media_storage(self):
        """
        Get the media storage object.
        
        Returns:
            Any: MediaStorage object or None if not connected.
        """
        return self.media_storage

    def get_media_pool(self):
        """
        Get the media pool object for the current project, refreshing it if needed.
        
        Returns:
            Any: MediaPool object or None if no project is open.
        """
        if self.current_project:
            self.media_pool = self.current_project.GetMediaPool()
        return self.media_pool

    def get_fusion(self):
        """
        Get the Fusion object for compositing tasks.
        
        Returns:
            Any: Fusion object or None if not connected.
        """
        return self.fusion

    def open_page(self, page_name: str) -> bool:
        """
        Open a specific page in DaVinci Resolve (e.g., "edit", "color").
        
        Args:
            page_name (str): The name of the page to open (valid: "media", "edit", "fusion", "color", "fairlight", "deliver").
        
        Returns:
            bool: True if successful, False if not connected or invalid page.
        """
        if not self.resolve:
            return False
        valid_pages = ["media", "edit", "fusion", "color", "fairlight", "deliver"]
        if page_name.lower() not in valid_pages:
            return False
        self.resolve.OpenPage(page_name.lower())  # Open the specified page
        return True

    def create_project(self, project_name: str) -> bool:
        """
        Create a new project with the given name.
        
        Args:
            project_name (str): Name of the project to create.
        
        Returns:
            bool: True if successful, False if project manager is unavailable or creation fails.
        """
        if not self.project_manager:
            return False
        new_project = self.project_manager.CreateProject(project_name)
        if new_project:  # If creation succeeds, update internal state
            self.current_project = new_project
            self.media_pool = self.current_project.GetMediaPool()
            return True
        return False

    def load_project(self, project_name: str) -> bool:
        """
        Load an existing project by name.
        
        Args:
            project_name (str): Name of the project to load.
        
        Returns:
            bool: True if successful, False if project manager is unavailable or project doesn't exist.
        """
        if not self.project_manager:
            return False
        loaded_project = self.project_manager.LoadProject(project_name)
        if loaded_project:  # If loading succeeds, update internal state
            self.current_project = loaded_project
            self.media_pool = self.current_project.GetMediaPool()
            return True
        return False

    def save_project(self) -> bool:
        """
        Save the current project.
        
        Returns:
            bool: True if successful, False if no project is open.
        """
        if not self.current_project:
            return False
        return self.current_project.SaveProject()

    def get_project_name(self) -> Optional[str]:
        """
        Get the name of the current project.
        
        Returns:
            Optional[str]: Project name or None if no project is open.
        """
        if not self.current_project:
            return None
        return self.current_project.GetName()

    def create_timeline(self, timeline_name: str) -> bool:
        """
        Create a new empty timeline in the current project.
        
        Args:
            timeline_name (str): Name of the timeline to create.
        
        Returns:
            bool: True if successful, False if media pool is unavailable or creation fails.
        """
        if not self.media_pool:
            return False
        new_timeline = self.media_pool.CreateEmptyTimeline(timeline_name)
        return new_timeline is not None

    def get_current_timeline(self):
        """
        Get the current timeline in the current project.
        
        Returns:
            Any: Timeline object or None if no project is open.
        """
        if not self.current_project:
            return None
        return self.current_project.GetCurrentTimeline()

    def get_timeline_count(self) -> int:
        """
        Get the number of timelines in the current project.
        
        Returns:
            int: Number of timelines, or 0 if no project is open.
        """
        if not self.current_project:
            return 0
        return self.current_project.GetTimelineCount()

    def get_timeline_by_index(self, index: int):
        """
        Get a timeline by its 1-based index.
        
        Args:
            index (int): 1-based index of the timeline.
        
        Returns:
            Any: Timeline object or None if no project or invalid index.
        """
        if not self.current_project:
            return None
        return self.current_project.GetTimelineByIndex(index)

    def set_current_timeline(self, timeline) -> bool:
        """
        Set the specified timeline as the current one.
        
        Args:
            timeline: Timeline object to set as current.
        
        Returns:
            bool: True if successful, False if no project is open.
        """
        if not self.current_project:
            return False
        return self.current_project.SetCurrentTimeline(timeline)

    def get_mounted_volumes(self) -> List[str]:
        """
        Get a list of mounted volumes in the media storage.
        
        Returns:
            List[str]: List of volume paths, empty if media storage is unavailable.
        """
        if not self.media_storage:
            return []
        return self.media_storage.GetMountedVolumes()

    def get_sub_folders(self, folder_path: str) -> List[str]:
        """
        Get a list of subfolders in the specified folder path.
        
        Args:
            folder_path (str): Path to the folder.
        
        Returns:
            List[str]: List of subfolder paths, empty if media storage is unavailable.
        """
        if not self.media_storage:
            return []
        return self.media_storage.GetSubFolders(folder_path)

    def get_files(self, folder_path: str) -> List[str]:
        """
        Get a list of files in the specified folder path.
        
        Args:
            folder_path (str): Path to the folder.
        
        Returns:
            List[str]: List of file paths, empty if media storage is unavailable.
        """
        if not self.media_storage:
            return []
        return self.media_storage.GetFiles(folder_path)

    def add_items_to_media_pool(self, file_paths: List[str]) -> List[Any]:
        """
        Add media files to the current media pool.
        
        Args:
            file_paths (List[str]): List of file paths to add.
        
        Returns:
            List[Any]: List of added media pool items, empty if media storage or pool is unavailable.
        """
        if not self.media_storage or not self.media_pool:
            return []
        return self.media_storage.AddItemsToMediaPool(file_paths)

    def get_root_folder(self):
        """
        Get the root folder of the media pool.
        
        Returns:
            Any: Root folder object or None if media pool is unavailable.
        """
        if not self.media_pool:
            return None
        return self.media_pool.GetRootFolder()

    def get_current_folder(self):
        """
        Get the current folder in the media pool.
        
        Returns:
            Any: Current folder object or None if media pool is unavailable.
        """
        if not self.media_pool:
            return None
        return self.media_pool.GetCurrentFolder()

    def add_sub_folder(self, parent_folder, folder_name: str):
        """
        Add a subfolder to the specified parent folder in the media pool.
        
        Args:
            parent_folder: Parent folder object.
            folder_name (str): Name of the subfolder to create.
        
        Returns:
            Any: Created subfolder object or None if media pool is unavailable or creation fails.
        """
        if not self.media_pool:
            return None
        return self.media_pool.AddSubFolder(parent_folder, folder_name)

    def get_folder_clips(self, folder) -> List[Any]:
        """
        Get a list of clips in the specified folder.
        
        Args:
            folder: Folder object.
        
        Returns:
            List[Any]: List of media pool items, empty if folder is invalid.
        """
        if not folder:
            return []
        return folder.GetClips()

    def get_folder_name(self, folder) -> Optional[str]:
        """
        Get the name of the specified folder.
        
        Args:
            folder: Folder object.
        
        Returns:
            Optional[str]: Folder name or None if folder is invalid.
        """
        if not folder:
            return None
        return folder.GetName()

    def get_folder_sub_folders(self, folder) -> List[Any]:
        """
        Get a list of subfolders in the specified folder.
        
        Args:
            folder: Folder object.
        
        Returns:
            List[Any]: List of subfolder objects, empty if folder is invalid.
        """
        if not folder:
            return []
        return folder.GetSubFolders()

    def append_to_timeline(self, clips: List[Any]) -> bool:
        """
        Append clips to the current timeline.
        
        Args:
            clips (List[Any]): List of media pool items to append.
        
        Returns:
            bool: True if successful, False if media pool is unavailable.
        """
        if not self.media_pool:
            return False
        return self.media_pool.AppendToTimeline(clips)

    def create_timeline_from_clips(self, timeline_name: str, clips: List[Any]):
        """
        Create a new timeline from the specified clips.
        
        Args:
            timeline_name (str): Name of the new timeline.
            clips (List[Any]): List of media pool items to include.
 ACC       Returns:
            Any: Created timeline object or None if media pool is unavailable.
        """
        if not self.media_pool:
            return None
        return self.media_pool.CreateTimelineFromClips(timeline_name, clips)

    def import_timeline_from_file(self, file_path: str):
        """
        Import a timeline from a file (e.g., XML, EDL).
        
        Args:
            file_path (str): Path to the timeline file.
        
        Returns:
            Any: Imported timeline object or None if media pool is unavailable.
        """
        if not self.media_pool:
            return None
        return self.media_pool.ImportTimelineFromFile(file_path)

    def execute_lua(self, script: str) -> Any:
        """
        Execute a Lua script in Resolve's Fusion environment.
        
        Args:
            script (str): Lua script to execute.
        
        Returns:
            Any: Result of the script execution or None if Fusion is unavailable.
        """
        if not self.fusion:
            return None
        return self.fusion.Execute(script)

def create_fusion_node(self, node_type: str, inputs: Dict[str, Any] = None) -> Any:
    """
    Create a new node in the current Fusion composition.
    
    Args:
        node_type (str): Type of node to create (e.g., "Blur", "ColorCorrector").
        inputs (Dict[str, Any], optional): Dictionary of input parameters for the node.
    
    Returns:
        Any: Created node object or None if Fusion or composition is unavailable.
    """
    try:
        comp = fusion.GetCurrentComp()
        if not comp:
            print("No Fusion composition found.")
            return None
            
        # Include position parameters (x, y)
        node = comp.AddTool(node_type, 0, 0)
        
        if not node:
            print(f"Error creating {node_type} node.")
            return None
            
        # Set input parameters if provided
        if inputs and node:
            for key, value in inputs.items():
                # Use SetInput method instead of dictionary-style assignment
                node.SetInput(key, value)
                
        print(f"{node_type} node created successfully.")
        return node
        
    except Exception as e:
        print(f"Error creating Fusion node: {e}")
        return None

    def get_current_comp(self) -> Any:
        """
        Get the current Fusion composition.
        
        Returns:
            Any: Current composition object or None if Fusion is unavailable.
        """
        if not self.fusion:
            return None
        try:
            return self.fusion.CurrentComp
        except Exception as e:
            logger.error(f"Error getting current composition: {e}")
            return None

    # New methods with enhanced functionality

    def get_timeline_items(self, track_type: str = "video", track_index: int = 1) -> List[Any]:
        """
        Get items (clips) from a specific track in the current timeline.
        
        Args:
            track_type (str): Type of track ("video", "audio", "subtitle"), defaults to "video".
            track_index (int): 1-based index of the track, defaults to 1.
        
        Returns:
            List[Any]: List of timeline items, empty if no timeline or track is invalid.
        """
        timeline = self.get_current_timeline()
        if not timeline:
            logger.warning("No current timeline available")
            return []
        try:
            items = timeline.GetItemListInTrack(track_type, track_index)
            return items if items else []
        except Exception as e:
            logger.error(f"Failed to get timeline items: {e}")
            return []

    def set_clip_property(self, clip, property_name: str, value: Any) -> bool:
        """
        Set a property on a timeline clip (e.g., "Pan", "ZoomX").
        
        Args:
            clip: Timeline item object.
            property_name (str): Name of the property to set.
            value: Value to assign to the property.
        
        Returns:
            bool: True if successful, False if clip is invalid or property set fails.
        """
        if not clip:
            return False
        try:
            return clip.SetProperty(property_name, value)
        except Exception as e:
            logger.error(f"Failed to set clip property {property_name}: {e}")
            return False

    def get_color_page_nodes(self) -> List[Any]:
        """
        Get all nodes in the current clip's color grade on the Color page.
        
        Returns:
            List[Any]: List of node objects, empty if no timeline or clip is available.
        """
        timeline = self.get_current_timeline()
        if not timeline:
            return []
        clip = timeline.GetCurrentVideoItem()
        if not clip:
            logger.warning("No current clip on Color page")
            return []
        try:
            return clip.GetNodeGraph().GetNodes()
        except Exception as e:
            logger.error(f"Failed to get color nodes: {e}")
            return []

    def add_color_node(self, node_type: str = "Corrector") -> Optional[Any]:
        """
        Add a new node to the current clip's color grade.
        
        Args:
            node_type (str): Type of node to add (e.g., "Corrector", "Layer"), defaults to "Corrector".
        
        Returns:
            Optional[Any]: Created node object or None if no timeline or clip is available.
        """
        timeline = self.get_current_timeline()
        if not timeline:
            return None
        clip = timeline.GetCurrentVideoItem()
        if not clip:
            return None
        try:
            node_graph = clip.GetNodeGraph()
            return node_graph.AddNode(node_type)
        except Exception as e:
            logger.error(f"Failed to add color node: {e}")
            return None

    def get_project_settings(self) -> Dict[str, Any]:
        """
        Get the current project's settings (e.g., frame rate, resolution).
        
        Returns:
            Dict[str, Any]: Dictionary of project settings, empty if no project is open.
        """
        if not self.current_project:
            return {}
        try:
            return self.current_project.GetSetting()
        except Exception as e:
            logger.error(f"Failed to get project settings: {e}")
            return {}

    def set_project_setting(self, key: str, value: Any) -> bool:
        """
        Set a specific project setting.
        
        Args:
            key (str): Setting key (e.g., "timelineFrameRate").
            value: Value to set for the key.
        
        Returns:
            bool: True if successful, False if no project or setting fails.
        """
        if not self.current_project:
            return False
        try:
            return self.current_project.SetSetting(key, value)
        except Exception as e:
            logger.error(f"Failed to set project setting {key}: {e}")
            return False

    def start_render(self, preset_name: str = None, render_path: str = None) -> bool:
        """
        Start rendering the current project with an optional preset and output path.
        
        Args:
            preset_name (str, optional): Name of the render preset to use.
            render_path (str, optional): Output directory for the render.
        
        Returns:
            bool: True if render starts successfully, False if no project or render fails.
        """
        if not self.current_project:
            return False
        try:
            if preset_name:
                self.current_project.LoadRenderPreset(preset_name)  # Load render preset if specified
            if render_path:
                self.current_project.SetRenderSettings({"TargetDir": render_path})  # Set output path
            return self.current_project.StartRendering()
        except Exception as e:
            logger.error(f"Failed to start render: {e}")
            return False

    def get_render_status(self) -> Dict[str, Any]:
        """
        Get the current render status of the project.
        
        Returns:
            Dict[str, Any]: Status info (e.g., "IsRenderInProgress", "CompletionPercentage"), empty if no project.
        """
        if not self.current_project:
            return {}
        try:
            return {
                "IsRenderInProgress": self.current_project.IsRenderingInProgress(),
                "CompletionPercentage": self.current_project.GetRenderingProgress()
            }
        except Exception as e:
            logger.error(f"Failed to get render status: {e}")
            return {}

    def add_timeline_marker(self, frame: int, color: str = "Blue", name: str = "", note: str = "") -> bool:
        """
        Add a marker to the current timeline at a specific frame.
        
        Args:
            frame (int): Frame number for the marker.
            color (str): Marker color (e.g., "Blue", "Red"), defaults to "Blue".
            name (str): Marker name, defaults to empty string.
            note (str): Marker note, defaults to empty string.
        
        Returns:
            bool: True if successful, False if no timeline or addition fails.
        """
        timeline = self.get_current_timeline()
        if not timeline:
            return False
        try:
            return timeline.AddMarker(frame, color, name, note, 1)  # Duration of 1 frame
        except Exception as e:
            logger.error(f"Failed to add marker: {e}")
            return False

    def get_clip_metadata(self, clip) -> Dict[str, Any]:
        """
        Get metadata for a specific clip (e.g., frame rate, resolution).
        
        Args:
            clip: Media pool item or timeline item.
        
        Returns:
            Dict[str, Any]: Metadata dictionary, empty if clip is invalid.
        """
        if not clip:
            return {}
        try:
            return clip.GetMetadata()
        except Exception as e:
            logger.error(f"Failed to get clip metadata: {e}")
            return {}

    def get_gallery(self) -> Any:
        """
        Get the Gallery object for the current project, used for managing stills and grades.
        
        Returns:
            Any: Gallery object or None if no project is open.
        """
        if not self.current_project:
            logger.warning("No current project available")
            return None
        try:
            return self.current_project.GetGallery()
        except Exception as e:
            logger.error(f"Failed to get gallery: {e}")
            return None

    def get_gallery_albums(self) -> List[Any]:
        """
        Get all albums in the gallery.
        
        Returns:
            List[Any]: List of GalleryAlbum objects, empty if gallery is unavailable.
        """
        gallery = self.get_gallery()
        if not gallery:
            return []
        try:
            return gallery.GetGalleryAlbumList()
        except Exception as e:
            logger.error(f"Failed to get gallery albums: {e}")
            return []

    def save_still(self, album_name: str = "Stills") -> Optional[Any]:
        """
        Save the current clip's grade as a still in the specified gallery album.
        
        Args:
            album_name (str): Name of the album to save the still in, defaults to "Stills".
        
        Returns:
            Optional[Any]: Saved GalleryStill object or None if saving fails.
        """
        gallery = self.get_gallery()
        timeline = self.get_current_timeline()
        if not gallery or not timeline:
            return None
        clip = timeline.GetCurrentVideoItem()
        if not clip:
            logger.warning("No current clip to save still from")
            return None
        try:
            album = gallery.GetAlbum(album_name)
            if not album:
                album = gallery.CreateEmptyAlbum(album_name)  # Create album if it doesn't exist
            return clip.SaveAsStill(album)
        except Exception as e:
            logger.error(f"Failed to save still: {e}")
            return None

    def apply_still(self, still, clip=None) -> bool:
        """
        Apply a still (grade) to a clip, defaulting to the current clip if none specified.
        
        Args:
            still: GalleryStill object to apply.
            clip: Timeline item to apply the still to (optional).
        
        Returns:
            bool: True if successful, False if still or clip is invalid.
        """
        if not still:
            return False
        target_clip = clip or self.get_current_timeline().GetCurrentVideoItem() if self.get_current_timeline() else None
        if not target_clip:
            logger.warning("No clip to apply still to")
            return False
        try:
            return target_clip.ApplyGradeFromStill(still)
        except Exception as e:
            logger.error(f"Failed to apply still: {e}")
            return False

    def add_track(self, track_type: str = "video") -> bool:
        """
        Add a new track to the current timeline.
        
        Args:
            track_type (str): Type of track to add ("video", "audio", "subtitle"), defaults to "video".
        
        Returns:
            bool: True if successful, False if no timeline or addition fails.
        """
        timeline = self.get_current_timeline()
        if not timeline:
            return False
        try:
            return timeline.AddTrack(track_type)
        except Exception as e:
            logger.error(f"Failed to add {track_type} track: {e}")
            return False

    def set_track_name(self, track_type: str, track_index: int, name: str) -> bool:
        """
        Set the name of a track in the current timeline.
        
        Args:
            track_type (str): Type of track ("video", "audio", "subtitle").
            track_index (int): 1-based index of the track.
            name (str): New name for the track.
        
        Returns:
            bool: True if successful, False if no timeline or naming fails.
        """
        timeline = self.get_current_timeline()
        if not timeline:
            return False
        try:
            return timeline.SetTrackName(track_type, track_index, name)
        except Exception as e:
            logger.error(f"Failed to set track name: {e}")
            return False

    def enable_track(self, track_type: str, track_index: int, enable: bool = True) -> bool:
        """
        Enable or disable a track in the current timeline.
        
        Args:
            track_type (str): Type of track ("video", "audio", "subtitle").
            track_index (int): 1-based index of the track.
            enable (bool): True to enable, False to disable, defaults to True.
        
        Returns:
            bool: True if successful, False if no timeline or enabling fails.
        """
        timeline = self.get_current_timeline()
        if not timeline:
            return False
        try:
            return timeline.SetTrackEnable(track_type, track_index, enable)
        except Exception as e:
            logger.error(f"Failed to set track enable state: {e}")
            return False

    def get_audio_volume(self, clip) -> Optional[float]:
        """
        Get the audio volume of a timeline clip.
        
        Args:
            clip: Timeline item with audio.
        
        Returns:
            Optional[float]: Volume level (e.g., 0.0 to 1.0) or None if clip is invalid.
        """
        if not clip:
            return None
        try:
            return clip.GetAudioVolume()
        except Exception as e:
            logger.error(f"Failed to get audio volume: {e}")
            return None

    def set_audio_volume(self, clip, volume: float) -> bool:
        """
        Set the audio volume of a timeline clip.
        
        Args:
            clip: Timeline item with audio.
            volume (float): Volume level to set (e.g., 0.0 to 1.0).
        
        Returns:
            bool: True if successful, False if clip is invalid or setting fails.
        """
        if not clip:
            return False
        try:
            return clip.SetAudioVolume(volume)
        except Exception as e:
            logger.error(f"Failed to set audio volume: {e}")
            return False

    def set_track_volume(self, track_index: int, volume: float) -> bool:
        """
        Set the volume of an audio track in the current timeline.
        
        Args:
            track_index (int): 1-based index of the audio track.
            volume (float): Volume level to set (e.g., 0.0 to 1.0).
        
        Returns:
            bool: True if successful, False if no timeline or setting fails.
        """
        timeline = self.get_current_timeline()
        if not timeline:
            return False
        try:
            return timeline.SetTrackVolume("audio", track_index, volume)
        except Exception as e:
            logger.error(f"Failed to set track volume: {e}")
            return False

    def get_version_count(self, clip, version_type: str = "color") -> int:
        """
        Get the number of versions (e.g., color grades) for a clip.
        
        Args:
            clip: Timeline item.
            version_type (str): Type of version ("color" or "fusion"), defaults to "color".
        
        Returns:
            int: Number of versions, 0 if clip is invalid.
        """
        if not clip:
            return 0
        try:
            return clip.GetVersionCount(version_type)
        except Exception as e:
            logger.error(f"Failed to get version count: {e}")
            return 0

    def set_current_version(self, clip, version_index: int, version_type: str = "color") -> bool:
        """
        Set the current version for a clip (e.g., switch between color grades).
        
        Args:
            clip: Timeline item.
            version_index (int): 0-based index of the version to set.
            version_type (str): Type of version ("color" or "fusion"), defaults to "color".
        
        Returns:
            bool: True if successful, False if clip is invalid or setting fails.
        """
        if not clip:
            return False
        try:
            return clip.SetCurrentVersion(version_index, version_type)
        except Exception as e:
            logger.error(f"Failed to set current version: {e}")
            return False

    def play(self) -> bool:
        """
        Start playback in DaVinci Resolve.
        
        Returns:
            bool: True if successful, False if not connected or playback fails.
        """
        if not self.resolve:
            return False
        try:
            self.resolve.Play()
            return True
        except Exception as e:
            logger.error(f"Failed to start playback: {e}")
            return False

    def stop(self) -> bool:
        """
        Stop playback in DaVinci Resolve.
        
        Returns:
            bool: True if successful, False if not connected or stop fails.
        """
        if not self.resolve:
            return False
        try:
            self.resolve.Stop()
            return True
        except Exception as e:
            logger.error(f"Failed to stop playback: {e}")
            return False

    def get_current_timecode(self) -> Optional[str]:
        """
        Get the current playback timecode in Resolve.
        
        Returns:
            Optional[str]: Timecode string (e.g., "01:00:00:00") or None if not connected.
        """
        if not self.resolve:
            return None
        try:
            return self.resolve.GetCurrentTimecode()
        except Exception as e:
            logger.error(f"Failed to get current timecode: {e}")
            return None

    def set_playhead_position(self, frame: int) -> bool:
        """
        Set the playhead position to a specific frame in the current timeline.
        
        Args:
            frame (int): Frame number to set the playhead to.
        
        Returns:
            bool: True if successful, False if no timeline or setting fails.
        """
        timeline = self.get_current_timeline()
        if not timeline:
            return False
        try:
            return timeline.SetCurrentTimecode(timeline.GetTimecodeFromFrame(frame))
        except Exception as e:
            logger.error(f"Failed to set playhead position: {e}")
            return False

    def export_project(self, project_name: str, file_path: str) -> bool:
        """
        Export a project to a file (e.g., .drp file).
        
        Args:
            project_name (str): Name of the project to export.
            file_path (str): Destination file path for the exported project.
        
        Returns:
            bool: True if successful, False if project manager is unavailable or export fails.
        """
        if not self.project_manager:
            return False
        try:
            return self.project_manager.ExportProject(project_name, file_path)
        except Exception as e:
            logger.error(f"Failed to export project: {e}")
            return False

    def import_project(self, file_path: str) -> bool:
        """
        Import a project from a file (e.g., .drp file).
        
        Args:
            file_path (str): Path to the project file to import.
        
        Returns:
            bool: True if successful, False if project manager is unavailable or import fails.
        """
        if not self.project_manager:
            return False
        try:
            return self.project_manager.ImportProject(file_path)
        except Exception as e:
            logger.error(f"Failed to import project: {e}")
            return False