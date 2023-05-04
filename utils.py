import pystac
from pathlib import Path
from dateutil.parser import parse


def create_in_memory_stac_hierarchy(root_dir, item_pattern='**/odc-metadata.stac-item.json', verbose=False):
    """
    Create STAC hierarchy for already existing STAC Items.

    Parameters
    ----------
    root_dir: Path
        Path to the root directory of the STAC hierarchy.
    item_pattern: str
        Pattern to find STAC Items. Default is '**/odc-metadata.stac-item.json'.
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
    
    for sub in root_dir.iterdir():
        if sub.is_dir() and len(sub.stem) == 7:
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
                    item = pystac.Item.from_file(href=str(item_p))
                    items.append(item)
                    collection.add_item(item=item)
                    
                    item.set_self_href(str(item_p))
                    for asset_key, asset in item.assets.items():
                        asset.href = Path(asset.href).name
                else:
                    continue
            
            extent = collection.extent.from_items(items=items)
            collection.extent = extent
            
            if verbose:
                print(f"{tile} - {len(stac_item_paths)}")
    
    return catalog


def filter_stac_collections(catalog, bbox, start_date, end_date):
    """
    Filter STAC Collections based on bounding box and time range.
    
    Parameters
    ----------
    catalog: pystac.Catalog
        The STAC Catalog to filter.
    bbox: list
        The bounding box to filter the STAC Collections.
    start_date: datetime.datetime
        The start date to filter the STAC Collections.
    end_date: datetime.datetime
        The end date to filter the STAC Collections.
    
    Returns
    -------
    filtered_collections: list
        The filtered STAC Collection IDs.
    """
    collections = catalog.get_all_collections()
    collections = list(collections)
    filtered_collections = []
    
    for collection in collections:
        spatial_extent = collection.extent.spatial.to_dict()
        temporal_extent = collection.extent.temporal.to_dict()
        
        collection_bbox = spatial_extent["bbox"][0]
        collection_time_range = temporal_extent["interval"][0]
        
        if (
                collection_bbox != [float("inf"), float("inf"), float("-inf"), float("-inf")] and
                bbox[0] <= collection_bbox[2] and
                bbox[2] >= collection_bbox[0] and
                bbox[1] <= collection_bbox[3] and
                bbox[3] >= collection_bbox[1] and
                start_date <= parse(collection_time_range[1]) and
                end_date >= parse(collection_time_range[0])
        ):
            filtered_collections.append(collection)
    
    filtered_collections = [coll.id for coll in filtered_collections]
    return filtered_collections
