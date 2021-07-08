import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import List
import logging

import click
import requests
from click.core import Context

logger = logging.getLogger(__name__)


@click.command(help="It downloads the specified images from the har.json file")
@click.option("--threads", default=2, help="No of Threads")
@click.option(
    "--file", default=Path("har.json"), help="File location of all the har content"
)
@click.option(
    "--directory",
    type=Path,
    default=Path(__file__).parent / "downloaded_img",
    help="Output directory of the downloaded files",
)
@click.option(
    "--regex", default="%2F(.*)\?", help="Regex used for filtering image filename"
)
@click.option("--log", default="INFO")
@click.pass_context
def main(
    ctx: Context, log: str, file: Path, directory: Path, threads: int, regex: str
) -> None:
    handle_logging(log_level=log)
    urls = har_extractor(file)
    filenames = filter_filenames(regex, urls, directory)
    images_download(urls, filenames, threads)
    logging.info("Download already finished!")
    logging.info("You can check the {} directory".format(directory))


def handle_logging(log_level) -> None:
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError("Invalid log level: %s" % log_level)
    logging.basicConfig(level=numeric_level)


def har_extractor(file: Path) -> List[str]:
    try:
        with open(file, "r") as file:
            har = json.load(file)
            image_urls = [
                entry["request"]["url"]
                for entry in har["log"]["entries"]
                if entry["response"]["content"]["mimeType"].startswith("image/")
            ]
            return image_urls
    except Exception as e:
        print(
            "Is your har.json file already filled with the data your want to download?"
        )
        sys.exit(1)


def filter_filenames(regex: str, urls: List[str], directory: Path) -> List[Path]:
    r = re.compile(regex)
    filenames = []

    try:
        directory.mkdir(parents=True, exist_ok=False)
    except FileExistsError as e:
        logging.error(e)
        logging.error(
            "Folder already exist, you may want to remove the content of the folder before continuing"
        )
        sys.exit(1)
    finally:
        logging.debug("Folder was created")

    for url in urls:
        result = r.search(url)
        if result:
            filenames.append(directory / result.group(1))
        else:
            filenames.append(directory / url.split("/")[-1])

    return filenames


def image_download_handler(url: str, filename: str) -> str:
    r = requests.get(url, stream=True)

    try:
        with open(filename, "w+b") as fp:
            fp.write(r.content)

        return "{} downloaded".format(filename)
    except FileNotFoundError as e:
        return "{} not downloaded".format(filename)


def images_download(urls: List[str], filenames: List[Path], threads: int) -> None:
    with ThreadPoolExecutor(max_workers=threads) as executor:
        results = executor.map(image_download_handler, urls, filenames)
    for result in results:
        logging.debug(result)


if __name__ == "__main__":

    main(obj={})
