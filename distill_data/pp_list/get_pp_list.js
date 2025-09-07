// Collect data from https://2024.cec.gov.tw/voteSearch/
// Select 縣市 and 行政區, press 查詢, and then paste the following code in the browser console. 

function get_csv() {
    let csv = ['PPID,VILLNAME,NEIGHBORHOODS'];
    for (el of Array.from(document.querySelector('#__layout > div > div.voteSearchContainer.container > div:nth-child(10) > div > div:nth-child(1) > ul').children)) {
        let pp_id = el.querySelector('div:nth-child(1) > span.space-r.tboxNo').innerText.trim();
        let pp_village = el.querySelector('div.tboxAddr > span:nth-child(2)').innerText;
        let pp_neighborhoods = el.querySelector('div.tboxAddr > span:nth-child(3)').innerText;
        if (pp_neighborhoods === '')
            pp_neighborhoods = '所有的鄰'
        csv.push(`${pp_id},${pp_village},"${pp_neighborhoods}"`);
    }
    csv.push('');
    return csv.join('\n');
}

function download(content, fileName, contentType) {
    let a = document.createElement('a');
    a.href = URL.createObjectURL(new Blob([content], {type: contentType}));
    a.download = fileName;
    a.click();
}

let title = document.querySelector("#__layout > div > div.voteSearchContainer.container > h2").innerText.trim();
download(get_csv(), `${title.replace(' ', '_')}_pp_list.csv`, 'text/plain');