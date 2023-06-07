from json.decoder import JSONDecodeError
from pathlib import Path
import re
from datetime import datetime
from shapely.geometry import box
import pytz
import pystac


def create_in_memory_stac_hierarchy(root_dir, item_pattern='**/odc-metadata.stac-item.json',
                                    collection_pattern='[SN]\d{2}[EW]\d{3}', verbose=False):
    """
    Create STAC hierarchy for already existing STAC Items.

    Parameters
    ----------
    root_dir: Path
        Path to the root directory of the STAC hierarchy.
    item_pattern: str
        Pattern to find STAC Items. Default is '**/odc-metadata.stac-item.json'.
    collection_pattern: str
        Pattern to find STAC Collections. Default is [S|N]\d{2}[E|W]\d{3}, e.g. 'S02E017'.
    verbose: bool
        If True, print the number of STAC Items per Collection. Default is False.

    Returns
    -------
    catalog: pystac.Catalog
        The in-memory STAC Catalog.
    """
    catalog = pystac.Catalog(id=f'{root_dir.stem}_catalog',
                             description=f'STAC Catalog for {root_dir.stem} products',
                             catalog_type=pystac.CatalogType.SELF_CONTAINED,
                             href=root_dir.joinpath('catalog.json'))
    sp_extent = pystac.SpatialExtent([None, None, None, None])
    tmp_extent = pystac.TemporalExtent([None, None])
    
    subdirs = [sub for sub in root_dir.iterdir() if re.match(collection_pattern, sub.name)]
    for sub in subdirs:
        tile = sub.stem
        stac_item_paths = list(sub.glob(item_pattern))
        
        collection = pystac.Collection(id=tile,
                                       description=f'STAC Collection for {root_dir.stem} products of tile {tile}.',
                                       extent=pystac.Extent(sp_extent, tmp_extent),
                                       href=sub.joinpath('collection.json'))
        catalog.add_child(collection)
        
        items = []
        for item_p in stac_item_paths:
            if tile in str(item_p.parent):
                try:
                    item = pystac.Item.from_file(href=str(item_p))
                except JSONDecodeError as e:
                    if verbose:
                        print(f"Could not read {item_p} in tile {tile} - Skip!")
                    continue
                
                items.append(item)
                collection.add_item(item=item)
                
                item.set_self_href(str(item_p))
                for asset_key, asset in item.assets.items():
                    asset.href = Path(asset.href).name
        
        extent = collection.extent.from_items(items=items)
        collection.extent = extent
        
        if verbose:
            print(f"{tile} - {len(stac_item_paths)}")
    
    return catalog


def timestring_to_utc_datetime(time, pattern):
    """ Convert time string to UTC datetime object.
    
    Parameters
    ----------
    time: str
        The time string to convert.
    pattern: str
        The format of the time string.
    
    Returns
    -------
    datetime: datetime.datetime
        The converted datetime object.
    """
    return datetime.strptime(time, pattern).replace(tzinfo=pytz.UTC)


def bbox_intersection(bbox1, bbox2):
    """
    Computes the intersection of two bounding boxes.

    Parameters
    ----------
    bbox1: list
        The first bounding box in the format [west, south, east, north].
    bbox2: list
        The second bounding box in the format [west, south, east, north].

    Returns
    -------
    intersection: list or None
        The intersection of the two bounding boxes in the format [west, south, east, north].
        Returns None if there is no intersection.
    """
    box1 = box(*bbox1)
    box2 = box(*bbox2)
    intersection = box1.intersection(box2)
    if intersection.is_empty:
        return None
    else:
        return list(intersection.bounds)


def filter_stac_catalog(catalog, bbox=None, time_range=None, time_pattern=None):
    """
    Filter STAC Catalog based on bounding box and time range.
    
    Parameters
    ----------
    catalog: pystac.Catalog
        The STAC Catalog to filter.
    bbox: list, optional
        The bounding box in the format [west, south, east, north]. Default is None, which means no spatial filtering is
        applied.
    time_range: tuple(str, str), optional
        The time range in the format (start_date, end_date). Default is None, which means no temporal filtering is
        applied.
    time_pattern: str, optional
        The format of the time strings used in time_range. Default is '%Y-%m-%d'. Only used if time_range is not None.
    
    Returns
    -------
    filtered_collections: list
        The filtered STAC Collections.
    filtered_items: list
        The filtered STAC Items.
    """
    if bbox is None:
        filtered_collections = [catalog.get_children()]
    else:
        filtered_collections = [collection for collection in catalog.get_children()
                                if collection.extent.spatial.bboxes is not None and
                                any(bbox_intersection(bbox, b) is not None
                                    for b in collection.extent.spatial.bboxes)]
    if time_range is None:
        filtered_items = []
        for collection in filtered_collections:
            filtered_items.append(collection.get_items())
    else:
        if time_pattern is None:
            time_pattern = '%Y-%m-%d'
        
        start_date = timestring_to_utc_datetime(time=time_range[0], pattern=time_pattern)
        end_date = timestring_to_utc_datetime(time=time_range[1], pattern=time_pattern)
        filtered_items = [item for collection in filtered_collections
                          for item in collection.get_items()
                          if start_date <= item.datetime <= end_date]
    
    return filtered_collections, filtered_items
