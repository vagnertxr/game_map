var wms_layers = [];


        var lyr_OpenStreetMap_0 = new ol.layer.Tile({
            'title': 'OpenStreetMap',
            //'type': 'base',
            'opacity': 1.000000,
            
            
            source: new ol.source.XYZ({
    attributions: ' ',
                url: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png'
            })
        });
var format_AverageRating_1 = new ol.format.GeoJSON();
var features_AverageRating_1 = format_AverageRating_1.readFeatures(json_AverageRating_1, 
            {dataProjection: 'EPSG:4326', featureProjection: 'EPSG:3857'});
var jsonSource_AverageRating_1 = new ol.source.Vector({
    attributions: ' ',
});
jsonSource_AverageRating_1.addFeatures(features_AverageRating_1);
var lyr_AverageRating_1 = new ol.layer.Vector({
                declutter: false,
                source:jsonSource_AverageRating_1, 
                style: style_AverageRating_1,
                popuplayertitle: "Average Rating",
                interactive: true,
    title: 'Average Rating<br />\
    <img src="styles/legend/AverageRating_1_0.png" /> No data<br />\
    <img src="styles/legend/AverageRating_1_1.png" /> 1138 - 1284<br />\
    <img src="styles/legend/AverageRating_1_2.png" /> 1284 - 1344<br />\
    <img src="styles/legend/AverageRating_1_3.png" /> 1344 - 1397<br />\
    <img src="styles/legend/AverageRating_1_4.png" /> 1397 - 1522<br />\
    <img src="styles/legend/AverageRating_1_5.png" /> 1522 - 1636<br />'
        });
var format_Playercount_2 = new ol.format.GeoJSON();
var features_Playercount_2 = format_Playercount_2.readFeatures(json_Playercount_2, 
            {dataProjection: 'EPSG:4326', featureProjection: 'EPSG:3857'});
var jsonSource_Playercount_2 = new ol.source.Vector({
    attributions: ' ',
});
jsonSource_Playercount_2.addFeatures(features_Playercount_2);
var lyr_Playercount_2 = new ol.layer.Vector({
                declutter: false,
                source:jsonSource_Playercount_2, 
                style: style_Playercount_2,
                popuplayertitle: "Player count",
                interactive: true,
    title: 'Player count<br />\
    <img src="styles/legend/Playercount_2_0.png" /> No data<br />\
    <img src="styles/legend/Playercount_2_1.png" /> 1 - 4<br />\
    <img src="styles/legend/Playercount_2_2.png" /> 4 - 7,2<br />\
    <img src="styles/legend/Playercount_2_3.png" /> 7,2 - 12,4<br />\
    <img src="styles/legend/Playercount_2_4.png" /> 12,4 - 25,8<br />\
    <img src="styles/legend/Playercount_2_5.png" /> 25,8 - 83<br />'
        });
var format_Mostcommonrank_3 = new ol.format.GeoJSON();
var features_Mostcommonrank_3 = format_Mostcommonrank_3.readFeatures(json_Mostcommonrank_3, 
            {dataProjection: 'EPSG:4326', featureProjection: 'EPSG:3857'});
var jsonSource_Mostcommonrank_3 = new ol.source.Vector({
    attributions: ' ',
});
jsonSource_Mostcommonrank_3.addFeatures(features_Mostcommonrank_3);
var lyr_Mostcommonrank_3 = new ol.layer.Vector({
                declutter: false,
                source:jsonSource_Mostcommonrank_3, 
                style: style_Mostcommonrank_3,
                popuplayertitle: "Most common rank",
                interactive: true,
    title: 'Most common rank<br />\
    <img src="styles/legend/Mostcommonrank_3_0.png" /> SILVER III<br />\
    <img src="styles/legend/Mostcommonrank_3_1.png" /> SILVER II<br />\
    <img src="styles/legend/Mostcommonrank_3_2.png" /> PLATINUM II<br />\
    <img src="styles/legend/Mostcommonrank_3_3.png" /> PLATINUM I<br />\
    <img src="styles/legend/Mostcommonrank_3_4.png" /> PENDING<br />\
    <img src="styles/legend/Mostcommonrank_3_5.png" /> GOLD I<br />\
    <img src="styles/legend/Mostcommonrank_3_6.png" /> BRONZE III<br />\
    <img src="styles/legend/Mostcommonrank_3_7.png" /> <br />'
        });

lyr_OpenStreetMap_0.setVisible(true);lyr_AverageRating_1.setVisible(true);lyr_Playercount_2.setVisible(true);lyr_Mostcommonrank_3.setVisible(true);
var layersList = [lyr_OpenStreetMap_0,lyr_AverageRating_1,lyr_Playercount_2,lyr_Mostcommonrank_3];
lyr_AverageRating_1.set('fieldAliases', {'fid': 'fid', 'countrycode': 'countrycode', 'Average rating': 'Average rating', 'Player count': 'Player count', 'Most common rank': 'Most common rank', 'pop_est': 'pop_est', 'continent': 'continent', 'Country name': 'Country name', 'iso_a3': 'iso_a3', 'gdp_md_est': 'gdp_md_est', });
lyr_Playercount_2.set('fieldAliases', {'fid': 'fid', 'countrycode': 'countrycode', 'Average rating': 'Average rating', 'Player count': 'Player count', 'Most common rank': 'Most common rank', 'pop_est': 'pop_est', 'continent': 'continent', 'Country name': 'Country name', 'iso_a3': 'iso_a3', 'gdp_md_est': 'gdp_md_est', });
lyr_Mostcommonrank_3.set('fieldAliases', {'fid': 'fid', 'countrycode': 'countrycode', 'Average rating': 'Average rating', 'Player count': 'Player count', 'Most common rank': 'Most common rank', 'pop_est': 'pop_est', 'continent': 'continent', 'Country name': 'Country name', 'iso_a3': 'iso_a3', 'gdp_md_est': 'gdp_md_est', });
lyr_AverageRating_1.set('fieldImages', {'fid': 'TextEdit', 'countrycode': 'TextEdit', 'Average rating': 'TextEdit', 'Player count': 'TextEdit', 'Most common rank': 'TextEdit', 'pop_est': 'TextEdit', 'continent': 'TextEdit', 'Country name': 'TextEdit', 'iso_a3': 'TextEdit', 'gdp_md_est': 'TextEdit', });
lyr_Playercount_2.set('fieldImages', {'fid': 'TextEdit', 'countrycode': 'TextEdit', 'Average rating': 'TextEdit', 'Player count': 'TextEdit', 'Most common rank': 'TextEdit', 'pop_est': 'TextEdit', 'continent': 'TextEdit', 'Country name': 'TextEdit', 'iso_a3': 'TextEdit', 'gdp_md_est': 'TextEdit', });
lyr_Mostcommonrank_3.set('fieldImages', {'fid': 'TextEdit', 'countrycode': 'TextEdit', 'Average rating': 'TextEdit', 'Player count': 'TextEdit', 'Most common rank': 'TextEdit', 'pop_est': 'TextEdit', 'continent': 'TextEdit', 'Country name': 'TextEdit', 'iso_a3': 'TextEdit', 'gdp_md_est': 'TextEdit', });
lyr_AverageRating_1.set('fieldLabels', {'fid': 'hidden field', 'countrycode': 'hidden field', 'Average rating': 'no label', 'Player count': 'hidden field', 'Most common rank': 'header label - always visible', 'pop_est': 'hidden field', 'continent': 'hidden field', 'Country name': 'header label - always visible', 'iso_a3': 'hidden field', 'gdp_md_est': 'hidden field', });
lyr_Playercount_2.set('fieldLabels', {'fid': 'hidden field', 'countrycode': 'hidden field', 'Average rating': 'hidden field', 'Player count': 'no label', 'Most common rank': 'hidden field', 'pop_est': 'hidden field', 'continent': 'hidden field', 'Country name': 'hidden field', 'iso_a3': 'hidden field', 'gdp_md_est': 'hidden field', });
lyr_Mostcommonrank_3.set('fieldLabels', {'fid': 'hidden field', 'countrycode': 'hidden field', 'Average rating': 'hidden field', 'Player count': 'hidden field', 'Most common rank': 'header label - visible with data', 'pop_est': 'hidden field', 'continent': 'hidden field', 'Country name': 'header label - visible with data', 'iso_a3': 'hidden field', 'gdp_md_est': 'hidden field', });
lyr_Mostcommonrank_3.on('precompose', function(evt) {
    evt.context.globalCompositeOperation = 'normal';
});