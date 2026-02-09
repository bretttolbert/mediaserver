import json
import os
import random
from typing import cast, Dict, List, Set
from urllib.parse import quote_plus  # type: ignore
from pathlib import Path
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


def filter_files(app: Flask, files: MediaFiles, artists: Artists, args: ArgsDict) -> List[MediaFile]:
    app.logger.info("filter_files args=%s", args_dict_to_str(args))

    ret: List[MediaFile] = []
    for f in files.files:
        # get artist associated with this file
        artist = None
        for a in artists.artists:
            if f.path.startswith(a.path):
                artist = a
                break
        if artist is None:
            app.logger.error(f"Failed to find artist for file '{f.path}'")

        # ArgTypeScalarInt:
        arg_type = ArgTypes.Scalar.Int.MinYear
        if arg_type in args:
            arg_value = cast(ArgValueScalarInt, args[arg_type])
            if arg_value and f.year < arg_value:
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
            if arg_value and f.year > arg_value:
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
        if artist is not None:
            country_code = artist.artist_data.country_code
            region_code = artist.artist_data.region_code
            city = artist.artist_data.city
        arg_type_list_file_value_map: Dict[ArgType, str] = {
            ArgTypes.List.Str.Artist: f.artist,
            ArgTypes.List.Str.AlbumArtist: f.albumartist,
            ArgTypes.List.Str.Album: f.album,
            ArgTypes.List.Str.Genre: f.genre,
            ArgTypes.List.Str.Title: f.title,
            ArgTypes.List.Str.Year: str(f.year),
            ArgTypes.List.Str.CountryCode: country_code,
            ArgTypes.List.Str.RegionCode: region_code,
            ArgTypes.List.Str.City: city,
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
            ret.append(f)
    return ret


def get_genres(files: MediaFiles) -> List[str]:
    ret: Set[str] = set()  # type: ignore
    for f in files.files:
        ret.add(f.genre)
    return sorted(ret)


def get_genre_counts(files: MediaFiles, sort: str) -> Dict[str, int]:
    ret: Dict[str, int] = {}
    for f in files.files:
        if f.genre in ret:
            ret[f.genre] += 1
        else:
            ret[f.genre] = 1
    if sort == "name":
        return dict(sorted(ret.items(), key=lambda item: item[0], reverse=False))
    else:  # default sort: by count
        return dict(sorted(ret.items(), key=lambda item: item[1], reverse=True))


def get_tracks(app: Flask, files: MediaFiles, artists: Artists, args: ArgsDict) -> List[MediaFile]:
    ret = filter_files(app, files, artists, args)

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
            ret = list(
                sorted(
                    ret,
                    key=lambda x: x.year,
                    reverse=True,
                )
            )
        elif sort == ArgValues.Scalar.Enum.Sort.Random:
            random.shuffle(ret)

    return ret


def get_artist_counts(app: Flask, files: MediaFiles, artists: Artists, args: ArgsDict) -> Dict[str, int]:
    ret: Dict[str, int] = {}

    files_filtered = filter_files(app, files, artists, args)
    for f in files_filtered:
        if f.artist in ret:
            ret[f.artist] += 1
        else:
            ret[f.artist] = 1

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


def get_artist_country_code_counts(app: Flask, artists: Artists, args: ArgsDict) -> Dict[str, int]:
    ret: Dict[str, int] = {}
    for artist in artists.artists:
        if artist.artist_data.country_code in ret:
            ret[artist.artist_data.country_code] += 1
        else:
            ret[artist.artist_data.country_code] = 1

    # default sort: by count
    items = sorted(ret.items(), key=lambda item: item[1], reverse=True)
    ret = dict(items)

    return ret


def get_artist_region_code_counts(app: Flask, artists: Artists, args: ArgsDict) -> Dict[str, int]:
    ret: Dict[str, int] = {}
    for artist in artists.artists:
        if artist.artist_data.region_code in ret:
            ret[artist.artist_data.region_code] += 1
        else:
            ret[artist.artist_data.region_code] = 1

    # default sort: by count
    items = sorted(ret.items(), key=lambda item: item[1], reverse=True)
    ret = dict(items)

    return ret


def get_artist_city_counts(app: Flask, artists: Artists, args: ArgsDict) -> Dict[str, int]:
    country_code_name_map = get_country_code_name_map(app)
    region_code_name_map = get_region_code_name_map(app)
    ret: Dict[str, int] = {}
    for artist in artists.artists:
        city_qualifiers = []
        if artist.artist_data.region_code in region_code_name_map:
            region_name = region_code_name_map[artist.artist_data.region_code]
            city_qualifiers.append(region_name)
        if artist.artist_data.country_code in country_code_name_map:
            country_name = country_code_name_map[artist.artist_data.country_code]
            city_qualifiers.append(country_name)
        city_uniq = artist.artist_data.city
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


def get_word_cloud_data_genres(files: MediaFiles) -> List[Dict[str, str]]:
    ret: List[Dict[str, str]] = []
    genres = get_genres(files)
    for g in genres:
        ret.append({"text": g})
    return ret


def get_artists(app: Flask, files: MediaFiles, artists: Artists, args: ArgsDict) -> List[str]:
    ret: Set[str] = set()  # type: ignore
    files_filtered = filter_files(app, files, artists, args)
    for f in files_filtered:
        ret.add(f.artist)
    return sorted(ret)


def get_word_cloud_data_artists(
    app: Flask, files: MediaFiles, artists: Artists, args: ArgsDict
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
    files: MediaFiles,
    artists: Artists,
    args: ArgsDict,
) -> List[AlbumInfo]:
    """Returns a list of one AlbumInfo per unique album"""
    album_set: Set[AlbumInfo] = set()  # type: ignore
    config = get_config(app)
    files_filtered = filter_files(app, files, artists, args)
    for f in files_filtered:
        # try to go with albumartist first, in order to better group files
        # in the same album together, but fallback to artist as key if
        # albumartist is not set
        artist = f.albumartist
        if not len(artist):
            artist = f.artist
        album_set.add(AlbumInfo(artist, f.album, f.year, get_cover_path(config, f)))

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
