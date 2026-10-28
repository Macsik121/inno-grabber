const tile_links = document.getElementsByClassName("aalink")
console.log(tile_links)
const urls = []
for (let a of tile_links) {
    urls.push(a.href)
}
console.log(urls)
