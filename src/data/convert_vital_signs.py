"""Export the Vital Signs geodatabase to a shapefile with numeric population fields."""
from pathlib import Path
import csv
import math
import re
import argparse
from src.utils.config import RAW_DIR, PROCESSED_DIR


def number(value):
    if value is None or not str(value).strip():
        return None
    result = float(str(value).strip().replace(',', ''))
    if not math.isfinite(result):
        raise ValueError(f'Non-finite population value: {value!r}')
    return result


def convert(source_path, output_dir):
    from osgeo import ogr

    ogr.UseExceptions()
    SOURCE = Path(source_path)
    OUTPUT = Path(output_dir)
    TARGET = OUTPUT / "vital_signs_population_tracts.shp"
    if OUTPUT.exists():
        raise FileExistsError(f'Refusing to overwrite {OUTPUT}')
    source = ogr.Open(str(SOURCE))
    if source is None or source.GetLayerCount() != 1:
        raise ValueError(f"Expected one readable layer in {SOURCE}")
    layer = source.GetLayer(0)
    fields = list(layer.schema)
    names = []
    used = set()
    for field in fields:
        name = field.GetName()
        short = name.replace('population_per_acre_', 'popac_').replace('population_', 'pop_')
        short = re.sub(r'[^A-Za-z0-9_]', '_', short)[:10]
        base, suffix = short, 1
        while short.lower() in used:
            tail = f'_{suffix}'
            short = base[:10-len(tail)] + tail
            suffix += 1
        used.add(short.lower())
        names.append(short)

    # Validate every conversion before creating the export.
    widths = [1] * len(fields)
    for feature in layer:
        for i, field in enumerate(fields):
            value = feature.GetField(i)
            if field.GetName().lower().startswith('population'):
                number(value)
            elif value is not None:
                widths[i] = max(widths[i], len(str(value).encode('utf-8')))
                if widths[i] > 254:
                    raise ValueError(f'Value exceeds shapefile text limit: {field.GetName()}')

    OUTPUT.mkdir(parents=True)
    destination = ogr.GetDriverByName('ESRI Shapefile').CreateDataSource(str(TARGET))
    out = destination.CreateLayer(TARGET.stem, layer.GetSpatialRef(), layer.GetGeomType(), options=['ENCODING=UTF-8'])
    mapping = []
    for i, field in enumerate(fields):
        numeric = field.GetName().lower().startswith('population')
        definition = ogr.FieldDefn(names[i], ogr.OFTReal if numeric else ogr.OFTString)
        definition.SetWidth(24 if numeric else widths[i])
        if numeric:
            definition.SetPrecision(10)
        out.CreateField(definition)
        mapping.append([field.GetName(), names[i], 'float' if numeric else 'text'])
    layer.ResetReading()
    for feature in layer:
        record = ogr.Feature(out.GetLayerDefn())
        record.SetGeometry(feature.GetGeometryRef())
        for i, field in enumerate(fields):
            value = feature.GetField(i)
            if field.GetName().lower().startswith('population'):
                value = number(value)
            elif value is not None:
                value = str(value)
            if value is not None:
                record.SetField(i, value)
        out.CreateFeature(record)
    out = None
    destination = None

    exported = ogr.Open(str(TARGET))
    check = exported.GetLayer(0)
    assert check.GetFeatureCount() == layer.GetFeatureCount()
    assert check.GetSpatialRef().IsSame(layer.GetSpatialRef())
    for i, field in enumerate(fields):
        if field.GetName().lower().startswith('population'):
            assert check.schema[i].GetType() == ogr.OFTReal
    layer.ResetReading()
    for original, saved in zip(layer, check):
        original_geometry = original.GetGeometryRef()
        saved_geometry = saved.GetGeometryRef()
        # Shapefile may reorder polygon rings; compare their spatial coverage.
        assert original_geometry.Equals(saved_geometry) or original_geometry.SymDifference(saved_geometry).IsEmpty()
        for i, field in enumerate(fields):
            expected = original.GetField(i)
            actual = saved.GetField(i)
            if field.GetName().lower().startswith('population'):
                expected = number(expected)
                assert (expected is None and actual is None) or (
                    expected is not None and actual is not None and
                    math.isclose(expected, actual, rel_tol=1e-12, abs_tol=1e-9)
                ), (field.GetName(), expected, actual)
            else:
                assert actual == (None if expected is None else str(expected))
    with (OUTPUT / 'field_name_lookup.csv').open('w', newline='', encoding='utf-8') as handle:
        writer = csv.writer(handle)
        writer.writerow(['original_field', 'shapefile_field', 'output_type'])
        writer.writerows(mapping)
    print(f'Created {TARGET}')
    print(f'Verified {check.GetFeatureCount()} features, geometry, CRS, all attributes, and numeric population fields.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=RAW_DIR / "Vital_signs_tracts_pop_estimate.gdb")
    parser.add_argument("--output-dir", type=Path, default=PROCESSED_DIR / "vital_signs_shapefile")
    args = parser.parse_args()
    convert(args.source, args.output_dir)


if __name__ == "__main__":
    main()
