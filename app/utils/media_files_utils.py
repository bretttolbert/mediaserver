import json
import os
import random
from typing import cast, Dict, List, Set
from urllib.parse import quote_plus  # type: ignore
from pathlib import Path
import pandas as pd
import sys
from flask.json import jsonify

from flask import Flask

from mediascan import Artists, MediaFiles, MediaFile

from app.types.config.mediaserver_config import MediaServerConfig
from app.types.arg_types import (
    args_dict_to_str,
    ArgsDict,
    ArgType,
    ArgTypes,
    ArgValues,
    ArgValueListStr,
    ArgValueScalarInt,
)
from app.types.album_info import AlbumInfo
from app.utils.string_utils import str_in_list_ignore_case
from app.utils.app_utils import get_config


def row_to_mediafile(row):
    mf = MediaFile(
        str(row.path),
        0,
        "mp3",
        str(row.title),
        str(row.artist),
        str(row.albumartist),
        str(row.album),
        str(row.genre),
        int(str(row.year)),
        0,
    )
    return mf


def df_to_mediafile_list(df: pd.DataFrame) -> List[MediaFile]:
    ret: List[MediaFile] = []
    for row in df.itertuples():
        ret.append(row_to_mediafile(row))
    return ret


def file_and_artist_paths_match(file_path: str, artist_path: str):
    """
    compare the artist and track (media file) paths
    this is is the most foolproof method,
    since we can assume a given file was scanned from a given artist directory
    if the leading part of the file path (i.e. the artist dir path) is identical.
    TODO: Add validation to ensure artist_name[0] matches ID3 tag albumartist value(s).

    # Prevent incomplete match e.g. these do not match:
    # "/data/Music/M"
    # "/data/Music/Municipal Waste/Hazardous Mutation [2005]/01 - Intro - Deathripper.mp3"
    """
    # below was SLOW:
    #   return str(Path(file_path).parent.parent) == artist_path
    # so now have this:
    tokens = file_path.split(os.sep)
    # leading slash results in first token being '', this ensures leading slash will be restored by the join
    file_artist_path = "/".join(tokens[:-2])
    # as processed above, file_artist_path will not have a trailing slash, so use startswith
    # just in case file_path has a trailing slash
    return artist_path.startswith(file_artist_path)


# These arguments require artist data from artists.yaml file (generated from artist.yaml files)
ARGS_REQUIRING_ARTIST = [ArgTypes.List.Str.CountryCode, ArgTypes.List.Str.RegionCode, ArgTypes.List.Str.City]


def filter_files(app: Flask, files: pd.DataFrame, artists: pd.DataFrame, args: ArgsDict) -> pd.DataFrame:
    app.logger.info("filter_files args=%s", args_dict_to_str(args))

    results = []
    for row in files.itertuples():
        # ArgTypeScalarInt:
        arg_type = ArgTypes.Scalar.Int.MinYear
        if arg_type in args:
            arg_value = cast(ArgValueScalarInt, args[arg_type])
            if arg_value and int(float(str(row.year))) < arg_value:
                app.logger.info(
                    "skipping file (value=%s) based on filter arg %s=%s",
                    arg_value,
                    arg_type,
                    arg_value,
                )
                app.logger.info("filter_files args=%s", args_dict_to_str(args))
                continue
        arg_type = ArgTypes.Scalar.Int.MaxYear
        if arg_type in args:
            arg_value = cast(ArgValueScalarInt, args[arg_type])
            if arg_value and int(float(str(row.year))) > arg_value:
                app.logger.info(
                    "skipping file (value=%s) based on filter arg %s=%s",
                    arg_value,
                    arg_type,
                    arg_value,
                )
                app.logger.info("filter_files args=%s", args_dict_to_str(args))
                continue
        # ArgTypeListStr:
        skip_file = False
        country_code = ""
        region_code = ""
        city = ""
        country_code = str(row.countrycode)
        region_code = str(row.regioncode)
        city = str(row.city)
        arg_type_list_file_value_map: Dict[ArgType, str] = {
            ArgTypes.List.Str.Artist: str(row.artist),
            ArgTypes.List.Str.AlbumArtist: str(row.albumartist),
            ArgTypes.List.Str.Album: str(row.album),
            ArgTypes.List.Str.Genre: str(row.genre),
            ArgTypes.List.Str.Title: str(row.title),
            ArgTypes.List.Str.Year: str(row.year),
            ArgTypes.List.Str.CountryCode: country_code,
            ArgTypes.List.Str.RegionCode: region_code,
            ArgTypes.List.Str.City: str(city),
        }
        for arg_type, file_value in arg_type_list_file_value_map.items():
            if arg_type in args:
                arg_value_list = cast(ArgValueListStr, args[arg_type])
                app.logger.info("filtering based on %s[] arg = [%s]", arg_type, arg_value_list)
                if len(arg_value_list) and not str_in_list_ignore_case(file_value, arg_value_list):
                    app.logger.info(
                        "skipping file (value=%s) based on %s[] arg = [%s]",
                        file_value,
                        arg_type,
                        arg_value_list,
                    )
                    app.logger.info("filter_files args=%s", args_dict_to_str(args))
                    skip_file = True
                    break
        if not skip_file:
            # app.logger.info("appending file %s", f)
            # app.logger.info("filter_files args=%s", args_dict_to_str(args))
            results.append(row)
    return pd.DataFrame(results)


def get_files_list(app: Flask, files: pd.DataFrame, artists: pd.DataFrame, args: ArgsDict) -> List[MediaFile]:
    files_list = filter_files(app, files, artists, args)
    return df_to_mediafile_list(files_list)


def get_genres(files: List[MediaFile]) -> List[str]:
    ret: Set[str] = set()  # type: ignore
    for f in files:
        ret.add(f.genre)
    return sorted(ret)


def get_genre_counts(files: pd.DataFrame, sort: str) -> Dict[str, int]:
    ret: Dict[str, int] = {}
    for f in files.itertuples():
        if str(f.genre) in ret:
            ret[str(f.genre)] += 1
        else:
            ret[str(f.genre)] = 1
    if sort == "name":
        return dict(sorted(ret.items(), key=lambda item: item[0], reverse=False))
    else:  # default sort: by count
        return dict(sorted(ret.items(), key=lambda item: item[1], reverse=True))


def get_tracks(app: Flask, files: pd.DataFrame, artists: pd.DataFrame, args: ArgsDict) -> List[MediaFile]:
    df = filter_files(app, files, artists, args)

    sort = ArgValues.Scalar.Enum.Sort.Random
    if ArgTypes.Scalar.Enum.Sort in args:
        sort = args[ArgTypes.Scalar.Enum.Sort]

    # Don't reorder tracks if displaying tracks for single album or a specific artist
    if (
        ArgTypes.List.Str.Album not in args
        and ArgTypes.List.Str.Artist not in args
        and ArgTypes.List.Str.AlbumArtist not in args
    ):
        if sort == ArgValues.Scalar.Enum.Sort.Year:
            """
            ret = list(
                sorted(
                    ret,
                    key=lambda x: getattr(x, "year"),
                    reverse=True,
                )
            )
            """
            df = df.sort_values(by="year", ascending=False)
        elif sort == ArgValues.Scalar.Enum.Sort.Random:
            # random.shuffle(ret)
            df = df.sample(frac=1)

    return df_to_mediafile_list(df)


def get_artist_counts(app: Flask, files: pd.DataFrame, artists: pd.DataFrame, args: ArgsDict) -> Dict[str, int]:
    ret: Dict[str, int] = {}

    files_filtered = filter_files(app, files, artists, args)
    for f in files_filtered.itertuples():
        if f.artist in ret:
            ret[str(f.artist)] += 1
        else:
            ret[str(f.artist)] = 1

    sort = ArgValues.Scalar.Enum.Sort.Year
    if ArgTypes.Scalar.Enum.Sort in args:
        sort = args[ArgTypes.Scalar.Enum.Sort]

    if sort == ArgValues.Scalar.Enum.Sort.Name:
        return dict(sorted(ret.items(), key=lambda item: item[0], reverse=False))
    elif sort == ArgValues.Scalar.Enum.Sort.Random:
        items = list(ret.items())
        random.shuffle(items)
        return dict(items)
    else:  # default sort: by count
        items = sorted(ret.items(), key=lambda item: item[1], reverse=True)
        ret = dict(items)

    return ret


def get_static_json_data(app: Flask, filename: str):
    if app.static_folder is None:
        sys.exit(1)
    full_path = os.path.join(app.static_folder, "json_data", filename)
    try:
        with open(full_path, "r") as json_file:
            return json.load(json_file)
    except FileNotFoundError:
        app.logger.error("Data file not found")
    except json.JSONDecodeError:
        app.logger.error("Could not decode JSON from file")
    return {}


def get_country_code_name_map(app: Flask) -> Dict[str, str]:
    return get_static_json_data(app, "country_code_name_map.json")


def get_region_code_name_map(app: Flask) -> Dict[str, str]:
    return get_static_json_data(app, "region_code_name_map.json")


def get_artist_country_code_counts(app: Flask, artists: pd.DataFrame, args: ArgsDict) -> Dict[str, int]:
    ret: Dict[str, int] = {}
    for artist in artists.itertuples():
        val = str(artist.countrycode)
        if val in ret:
            ret[val] += 1
        else:
            ret[val] = 1

    # default sort: by count
    items = sorted(ret.items(), key=lambda item: item[1], reverse=True)
    ret = dict(items)

    return ret


def get_artist_region_code_counts(app: Flask, artists: pd.DataFrame, args: ArgsDict) -> Dict[str, int]:
    ret: Dict[str, int] = {}
    for artist in artists.itertuples():
        val = str(artist.regioncode)
        if val in ret:
            ret[val] += 1
        else:
            ret[val] = 1

    # default sort: by count
    items = sorted(ret.items(), key=lambda item: item[1], reverse=True)
    ret = dict(items)

    return ret


def get_artist_city_counts(app: Flask, artists: pd.DataFrame, args: ArgsDict) -> Dict[str, int]:
    country_code_name_map = get_country_code_name_map(app)
    region_code_name_map = get_region_code_name_map(app)
    ret: Dict[str, int] = {}
    for artist in artists.itertuples():
        city_qualifiers = []
        cc = str(artist.countrycode)
        rc = str(artist.regioncode)
        if rc in region_code_name_map:
            region_name = region_code_name_map[rc]
            city_qualifiers.append(region_name)
        if cc in country_code_name_map:
            country_name = country_code_name_map[cc]
            city_qualifiers.append(country_name)
        city_uniq = str(artist.city)
        if len(city_qualifiers):
            city_uniq = f"{city_uniq} ({', '.join(city_qualifiers)})"
        if city_uniq in ret:
            ret[city_uniq] += 1
        else:
            ret[city_uniq] = 1

    # default sort: by count
    items = sorted(ret.items(), key=lambda item: item[1], reverse=True)
    ret = dict(items)

    return ret


def get_word_cloud_data_genres(files: pd.DataFrame) -> List[Dict[str, str]]:
    ret: List[Dict[str, str]] = []
    genres = get_genres(df_to_mediafile_list(files))
    for g in genres:
        ret.append({"text": g})
    return ret


def get_artists(app: Flask, files: pd.DataFrame, artists: pd.DataFrame, args: ArgsDict) -> List[str]:
    ret: Set[str] = set()  # type: ignore
    files_filtered = filter_files(app, files, artists, args)
    for f in files_filtered.itertuples():
        ret.add(str(f.artist))
    return sorted(ret)


def get_word_cloud_data_artists(
    app: Flask, files: pd.DataFrame, artists: pd.DataFrame, args: ArgsDict
) -> List[Dict[str, str]]:
    ret: List[Dict[str, str]] = []
    artists_filtered = get_artists(app, files, artists, args)
    for a in artists_filtered:
        ret.append({"text": a})
    return ret


def get_cover_path(config: MediaServerConfig, file: MediaFile) -> Path:
    dir_path = Path(file.path.replace(os.path.basename(file.path), ""))
    if config.album_covers_path != config.playback_methods.local.media_path:
        # e.g. "/data/Music/Logic/Orville%20[2022]/cover.jpg"
        # config.playback_methods.local.media_path = "/data/Music/"
        # config.album_covers_path = "/var/www/html/Covers/"
        dir_path = Path(str(dir_path).replace(config.playback_methods.local.media_path, config.album_covers_path))
    return dir_path / "cover.jpg"


def get_albums(
    app: Flask,
    files: pd.DataFrame,
    artists: pd.DataFrame,
    args: ArgsDict,
) -> List[AlbumInfo]:
    """Returns a list of one AlbumInfo per unique album"""
    album_set: Set[AlbumInfo] = set()  # type: ignore
    config = get_config(app)
    files_filtered = filter_files(app, files, artists, args)
    for f in files_filtered.itertuples():
        # try to go with albumartist first, in order to better group files
        # in the same album together, but fallback to artist as key if
        # albumartist is not set
        artist = str(f.albumartist)
        if not len(artist):
            artist = str(f.artist)
        album_set.add(
            AlbumInfo(artist, str(f.album), int(float(str(f.year))), get_cover_path(config, row_to_mediafile(f)))
        )

    ret: List[AlbumInfo] = list(album_set)
    sort = ArgValues.Scalar.Enum.Sort.Random
    if ArgTypes.Scalar.Enum.Sort in args:
        sort = args[ArgTypes.Scalar.Enum.Sort]

    if sort == ArgValues.Scalar.Enum.Sort.Artist:
        ret = sorted(ret, key=lambda album: album.artist)
    elif sort == ArgValues.Scalar.Enum.Sort.Album:
        ret = sorted(ret, key=lambda album: album.album)
    elif sort == ArgValues.Scalar.Enum.Sort.Year:
        # sort by year (descending)
        ret = sorted(ret, key=lambda album: album.year, reverse=True)
    elif sort == ArgValues.Scalar.Enum.Sort.Random:
        random.shuffle(ret)

    # now that we have it sorted as specified, slice if necessary to keep the
    # result count below the configured max results limit for album covers
    if config.max_results_album_covers > 0 and len(ret) > config.max_results_album_covers:
        ret = ret[: config.max_results_album_covers]

    return ret
