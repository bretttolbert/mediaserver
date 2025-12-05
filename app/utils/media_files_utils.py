import os
from typing import cast, Dict, List
from urllib.parse import quote_plus  # type: ignore
from pathlib import Path

from flask import Flask

from mediascan import MediaFiles, MediaFile

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


def filter_files(app: Flask, files: MediaFiles, args: ArgsDict) -> List[MediaFile]:
    app.logger.debug("filter_files args=%s", args_dict_to_str(args))

    ret: List[MediaFile] = []
    for f in files.files:
        # ArgTypeScalarInt:
        arg_type = ArgTypes.Scalar.Int.MinYear
        if arg_type in args:
            arg_value = cast(ArgValueScalarInt, args[arg_type])
            if arg_value and f.year < arg_value:
                app.logger.debug(
                    "skipping file (value=%s) based on filter arg %s=%s",
                    arg_value,
                    arg_type,
                    arg_value,
                )
                app.logger.debug("filter_files args=%s", args_dict_to_str(args))
                continue
        arg_type = ArgTypes.Scalar.Int.MaxYear
        if arg_type in args:
            arg_value = cast(ArgValueScalarInt, args[arg_type])
            if arg_value and f.year > arg_value:
                app.logger.debug(
                    "skipping file (value=%s) based on filter arg %s=%s",
                    arg_value,
                    arg_type,
                    arg_value,
                )
                app.logger.debug("filter_files args=%s", args_dict_to_str(args))
                continue
        # ArgTypeListStr:
        skip_file = False
        arg_type_list_file_value_map: Dict[ArgType, str] = {
            ArgTypes.List.Str.Artist: f.artist,
            ArgTypes.List.Str.AlbumArtist: f.albumartist,
            ArgTypes.List.Str.Album: f.album,
            ArgTypes.List.Str.Genre: f.genre,
            ArgTypes.List.Str.Title: f.title,
            ArgTypes.List.Str.Year: str(f.year),
        }
        for arg_type, file_value in arg_type_list_file_value_map.items():
            if arg_type in args:
                arg_value_list = cast(ArgValueListStr, args[arg_type])
                app.logger.debug(
                    "filtering based on %s[] arg = [%s]", arg_type, arg_value_list
                )
                if len(arg_value_list) and not str_in_list_ignore_case(
                    file_value, arg_value_list
                ):
                    app.logger.debug(
                        "skipping file (value=%s) based on %s[] arg = [%s]",
                        file_value,
                        arg_type,
                        arg_value_list,
                    )
                    app.logger.debug("filter_files args=%s", args_dict_to_str(args))
                    skip_file = True
                    break
        if not skip_file:
            # app.logger.debug("appending file %s", f)
            # app.logger.debug("filter_files args=%s", args_dict_to_str(args))
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


def get_artist_counts(
    app: Flask, files: MediaFiles, args: ArgsDict, sort: str
) -> Dict[str, int]:
    ret: Dict[str, int] = {}
    files_filtered = filter_files(app, files, args)
    for f in files_filtered:
        if f.artist in ret:
            ret[f.artist] += 1
        else:
            ret[f.artist] = 1
    if sort == ArgValues.Scalar.Enum.Sort.Name:
        return dict(sorted(ret.items(), key=lambda item: item[0], reverse=False))
    else:  # default sort: by count
        return dict(sorted(ret.items(), key=lambda item: item[1], reverse=True))


def get_genre_urls(files: MediaFiles) -> List[Dict[str, str]]:
    ret: List[Dict[str, str]] = []
    genres = get_genres(files)
    for g in genres:
        ret.append({"text": g, "url": f"/artists-cloud?genre={quote_plus(g)}"})
    return ret


def get_artists(app: Flask, files: MediaFiles, args: ArgsDict) -> List[str]:
    ret: Set[str] = set()  # type: ignore
    files_filtered = filter_files(app, files, args)
    for f in files_filtered:
        ret.add(f.artist)
    return sorted(ret)


def get_artist_urls(
    app: Flask, files: MediaFiles, args: ArgsDict
) -> List[Dict[str, str]]:
    ret: List[Dict[str, str]] = []
    artists = get_artists(app, files, args)
    for a in artists:
        ret.append({"text": a, "url": f"/albums?artist={quote_plus(a)}"})
    return ret


def get_cover_path(file: MediaFile, config: MediaServerConfig) -> Path:
    dir_path = Path(file.path.replace(os.path.basename(file.path), ""))
    return dir_path / "cover.jpg"


def get_albums(
    app: Flask,
    files: MediaFiles,
    args: ArgsDict,
) -> List[AlbumInfo]:
    """Returns a list of one AlbumInfo per unique album"""
    ret: Set[AlbumInfo] = set()  # type: ignore
    config = app.config["MEDIASERVER_CONFIG"]
    files_filtered = filter_files(app, files, args)
    for f in files_filtered:
        # try to go with albumartist first, in order to better group files
        # in the same album together, but fallback to artist as key if
        # albumartist is not set
        artist = f.albumartist
        if not len(artist):
            artist = f.artist
        ret.add(AlbumInfo(artist, f.album, f.year, get_cover_path(f, config)))
    sort = ArgValues.Scalar.Enum.Sort.Year
    if ArgTypes.Scalar.Enum.Sort in args:
        sort = args[ArgTypes.Scalar.Enum.Sort]

    if sort == ArgValues.Scalar.Enum.Sort.Artist:
        return sorted(ret, key=lambda album: album.artist)
    if sort == ArgValues.Scalar.Enum.Sort.Album:
        return sorted(ret, key=lambda album: album.album)
    else:  # default: sort by year (descending)
        return sorted(ret, key=lambda album: album.year, reverse=True)
