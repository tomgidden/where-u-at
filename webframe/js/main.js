var Calendar, Clock, People;

var weather_data;
var cal_data;
var loc_data = [];
var leds_data = [];

function mqtt_message(topic, payload, details)
{
    payload = payload.toString();

    if (0 === topic.indexOf('/location')) {
        location_update(topic, payload, details);
        times_render();
    }
    else if (0 === topic.indexOf('/calendar')) {
        calendar_update(topic, payload, details);
        weather_render();
        times_render();
    }
    else if (0 === topic.indexOf('/weather')) {
        calendar_render();
        weather_update(topic, payload, details);
        times_render();
    }
    else {
        var g = topic.match('/sensor/(.+)/state');
        if (g) {
            leds_update(g[1], payload);
        }
    }
}

function map_toggle(ev)
{
    var person = $(ev.currentTarget);

    var position = {lat: person.data('latitude'), lng: person.data('longitude')};

    var parent = $('#map_parent');

    if ($('#map').length !== 0) {
        parent.fadeOut('slow', function () { $('#map').remove(); });
    }
    else {
        map = $('<div>').prop('id', 'map').appendTo(parent);

        gmap = new google.maps.Map(document.getElementById('map'), {
            zoom: 17,
            center: position,
            mapTypeId: 'terrain',
            styles: mapstyle
        });

        new google.maps.Marker({
            position: position,
            map: gmap,
            label: person.data('label')
        });

        parent.fadeIn('slow');
    }
}

function calendar_set_day(parent, date, events, title, cls)
{
    var id = date.format('YYYYMMDD');

    var day_el, title_el, weather_el;

    // Get/Create day element
    if ( ! (day_el = $('.day_'+id)).length ) {
        day_el = $('<div>').appendTo(parent);
    }

    // Set title text if not explicit
    if (!title)
        title = date.format('dddd, D MMMM');

    // Reset classes on day element.  This will also unflag the day if it
    // was marked for deletion (good)
    day_el.prop('class', 'day day_'+id);
    if (cls) day_el.addClass(cls);

    // Get/Create weather element
    if ( ! (weather_el = $('.weather', day_el)).length ) {
        weather_el = $('<div>')
            .addClass('weather')
            .appendTo(day_el);
    }

    // Clear all events.  Easier this way.
    $('.event', day_el).remove();

    // Add events back in
    if (events) {
        for (var i in events) {
            if (!events.hasOwnProperty(i)) continue;
            var event = events[i];

            var event_el = $('<div>')
                .addClass('event');

            if (! event.allday ) {
                $('<div>')
                    .addClass('time format')
                    .data('time', event.begin)
                    .data('format', 'HH:mm')
                    .appendTo(event_el);
            }
            else {
                $('<div>')
                    .addClass('time allday')
                    .text('---')
                    .appendTo(event_el);
            }

            description = event.title.replace(/^\d{1,2}:\d{2}\s+/, '');

            m = description.match(/^\[(.+)\]$/);
            if (m) {
                description = m[1];
                event_el.addClass('holiday');
                event_el.prependTo(day_el);
            }
            else {
                event_el.appendTo(day_el);
            }

            $('<div>')
                .addClass('description')
                .text(description)
                .appendTo(event_el);
        }
    }
    else {
        $('<div>')
            .addClass('event noevents')
            .text('No events scheduled')
            .appendTo(day_el);

        day_el.addClass('noevents');
    }

    // Get/Create title element
    $('heading', day_el).remove();
    title_el = $('<heading>')
        .addClass('title')
        .text(title)
        .prependTo(day_el);
}

function calendar_resolve(payload)
{
    var events = [];
    var now = moment();

    for (var i in payload) {
        if (!payload.hasOwnProperty(i)) continue;

        var event = payload[i];

        // event.begin = event.begin.replace(/([\-\+]\d\d):01$/, '$1:00');
        event.begin = moment(event.begin);

        if (event.begin.isBefore(now, 'day')) continue;

        event.end = moment(event.end);

        var ymd = event.begin.format('YYYYMMDD')
        event.ymd = ymd;

        if (undefined === events[ymd]) {
            events[ymd] = [ event ];
        } else {
            events[ymd].push(event);
        }
    }

    return events;
}

function leds_update(sensor, payload)
{
    if (typeof payload === 'string')
        payload = JSON.parse(payload);

    if (undefined !== leds_data[sensor] && 1===leds_data[sensor] && !payload) {
        // Change to flash
        leds_data[sensor] = 2;
        setTimeout(function () { leds_update(sensor, false); }, 120*1000);
    }
    else {
        leds_data[sensor] = payload ? 1 : 0;
    }

    leds_render();
}

function leds_render()
{
    leds_render_led('washingmachine');
    leds_render_led('tumbledryer');
}

function leds_render_led(sensor)
{
    var obj = $('#led_'+sensor);
    var cur = obj.data('state');
    console.log("Sensor "+sensor+" "+cur+" -> "+leds_data[sensor]);

    if (cur != leds_data[sensor]) {
        if (1 === leds_data[sensor]) {
            obj.show().removeClass('flash');
        }
        else if (0 === leds_data[sensor]) {
            obj.hide().removeClass('flash');
        }
        else if (2 === leds_data[sensor]) {
            obj.show().addClass('flash');
        }
        obj.data('state', leds_data[sensor]);
    }
}

function weather_update(topic, payload, details)
{
    payload = JSON.parse(payload);
    weather_data = payload['list'];
    weather_render();
}

function weather_toggle()
{
    $('body').toggleClass('hideweather');
}

function weather_render()
{
    if (!weather_data) return;

    var now = moment();
    var primary_fc = [];          // Primary forecast for a day

    $('.weather').empty();

    for (var i in weather_data) {
        if (!weather_data.hasOwnProperty(i)) continue;
        var fc = weather_data[i];

        var dt = moment(fc['dt_txt']);
        var id = dt.format('YYYYMMDD');

        var day_el = $('.day_'+id);
        if (day_el.length <= 0) continue;

        var weather_el = $('.weather', day_el);
        var h = dt.hour();
//        if (h < 9 || h > 21) continue;

        var fc_el = $('<div>').addClass('forecast').appendTo(weather_el);

        fc_el.on('click', weather_toggle);

        if (dt < now) fc_el.addClass('past');

        if (undefined===primary_fc[id] || 12===h)
            primary_fc[id] = fc_el;

        fc_el.addClass('flagged');

        $('<span>').addClass('at').text(dt.format('ha')).appendTo(fc_el);
        $('<i>').addClass('wi wi-owm-'+fc['weather'][0]['id']).text(fc['weather'][0]['description']).appendTo(fc_el);
        $('<span>').addClass('temperature').text(Math.round(fc['main']['temp']-273.15)).appendTo(fc_el);
    }

    for (var i in primary_fc)
        if (primary_fc.hasOwnProperty(i))
            primary_fc[i].addClass('primary');
}

function calendar_update(topic, payload, details)
{
    cal_data = JSON.parse(payload);
    calendar_render();
}

function calendar_render()
{
    if (!cal_data) return;

    var days = calendar_resolve(cal_data);

    // Get/Create parent
    var parent;
    if ( ! (parent = $('div.events')).length ) {
        parent = $('<div>')
            .addClass('events')
            .appendTo(Calendar);
    }

    // Flag all days as candidates for deletion.  calendar_set_day()
    // resets the classes, having the effect of unflagging days that are
    // still relevant.
    $('.day', parent).addClass('flagged');

    var t = moment();
    var ymd = t.format('YYYYMMDD');

    // Add today, tomorrow and the following three days, regardless of
    // events, so weather can be displayed.
    calendar_set_day(parent,
                     t,
                     undefined !== days[ymd] ? days[ymd] : null,
                     moment().format('dddd, D MMMM YYYY'),
                     'today');

    ymd = t.add(1, 'days').format('YYYYMMDD');

    calendar_set_day(parent,
                     t,
                     undefined !== days[ymd] ? days[ymd] : null,
                     'Tomorrow',
                     'tomorrow');

    ymd = t.add(1, 'days').format('YYYYMMDD');

    for (var x=2; x<7; x++) {

        calendar_set_day(parent,
                         t,
                         undefined !== days[ymd] ? days[ymd] : null);

        ymd = t.add(1, 'days').format('YYYYMMDD');
    }

    // And add any extra days with events
    for (var d in days) {
        if (!days.hasOwnProperty(d)) continue;

        var t2 = moment(d);
        if (t2.isBefore(t)) continue;

        calendar_set_day(parent, t2, days[d], null);
    }

    // Remove any days that remain flagged
    $('.flagged', parent).remove();
}

function times_render()
{
    $('.time.since').each(function (ix, el) {
        el = $(el);
        var t = moment.duration(moment(el.data('time')) - moment.now());
        el.text( t.humanize(true) );
    });

    $('.time.format').each(function (ix, el) {
        el = $(el);
        var t = moment.duration(moment(el.data('time')) - moment.now());
        el.text( moment(el.data('time')).format(el.data('format')) );
    });

    Clock.text(moment().format('h:mm a'));
}

function location_update(topic, payload, details)
{
    payload = JSON.parse(payload);
    loc_data[payload.id] = payload;
    person_render(payload);
}

function location_render()
{
    if (loc_data.length < 1) return;

    for (var i in loc_data) {
        if (!loc_data.hasOwnProperty(i)) continue;
        person_render(loc_data[i]);
    }
}

function person_render(payload)
{
    payload.distance = distance_from_home(payload.latitude, payload.longitude);
    //payload.since = moment(payload.time).format('ddd, h:MM a');
    //payload.since = "Since: "+moment.duration(moment(payload.time)-moment.now()).humanize(true);

    payload.address = payload.address.replace(/([A-Z]{1,2}\d{1,2}[A-Z]?)\s*(\d[A-Z]{2})/, '$1\xa0$2');

    if (! (person = $('#'+payload.id, People) ).length ) {
        person = $('<div>').addClass('person').prop('id', payload.id).appendTo(People);
        person.on('click', map_toggle);
    }

    if (! (nickname = $('.nickname', person) ).length )
        nickname = $('<heading>').addClass('nickname').appendTo(person);
    nickname.text(payload.nickname);

    if (! (address = $('.address', person) ).length )
        address = $('<div>').addClass('address').appendTo(person);

    if (payload.address)
        address.text(payload.address);
    else if (payload.raw_address)
        address.text(payload.raw_address);
    else
        address.text(latlon_to_dms(payload.latitude, payload.longitude))

    if (! (distance = $('.distance', person) ).length )
        distance = $('<div>').addClass('distance').appendTo(person);

    if (payload.address === 'Home') {
        distance.text('HOME');
        person.addClass('athome');
    } else {
        distance.text(payload.distance);
        person.removeClass('athome');
    }

    if (! (accuracy = $('.accuracy', person) ).length )
        accuracy = $('<div>').addClass('accuracy').appendTo(person);
    accuracy.text('± ' + payload.accuracy + 'm');

    person.data('latitude', payload.latitude);
    person.data('longitude', payload.longitude);
    person.data('label', payload.nickname.substr(0,1));

    if (! (since = $('.since', person) ).length )
        since = $('<div>').addClass('time since').appendTo(person);

    since.data('time', payload.time);
}

function precisionRound(number, precision) {
    var factor = Math.pow(10, precision);
    return Math.round(number * factor) / factor;
}

function distance_from_home(lat, lon)
{
    hlat = 51.4903304;
    hlon = -2.7640536;
    theta = hlon - lon;
    dist = Math.sin(lat*3.1415927/180.0) * Math.sin(hlat*3.1415927/180.0) + Math.cos(lat*3.1415927/180.0) * Math.cos(hlat*3.1415927/180.0) * Math.cos(theta*3.1415927/180.0);
    dist = Math.acos(dist);
    dist = dist*180.0/3.1415927;
    metres = dist * 60 *  1853;
    miles = metres * 0.000621371;

    //if (miles <= 0.1)
    //  return "here";
    //if (metres < 804)
    //  return Math.round(metres) + " metres";
    if (miles < 0.1)
        return "HOME";
    else if (miles < 100)
        return precisionRound(miles, 1) + " mi";
    else
        return Math.round(miles+0.5) + " mi";
}

function latlon_to_dms(lat, lon)
{
    if (undefined===lat || undefined===lon)
        return "";

    lad = 'N';
    if (lat < 0) {
        lad = 'S';
        lat = -lat;
    }

    lai = Math.trunc(lat);
    laf = Math.abs(lat - lai);
    tmp = laf * 3600;
    lam = Math.trunc(tmp/60);
    las = tmp - lam*60;

    lod = 'E';
    if (lon < 0) {
        lod = 'W';
        lon = -lon;
    }

    loi = Math.trunc(lon);
    lof = Math.abs(lon - loi);

    tmp = lof * 3600;
    lom = Math.trunc(tmp/60);
    los = tmp - lom*60;

    return (
        lai + "° " + lam + "' " + precisionRound(las,2) + '" ' + lad + ', ' +
            loi + "° " + lom + "' " + precisionRound(los,2) + '" ' + lod
    );
}

$(function () {

    Clock = $('#clock');
    Calendar = $('#calendar');
    People = $('#people');

    $('body').addClass('hideweather');

    times_render();

    setInterval(weather_render, 60*30*1000);
    setInterval(calendar_render, 60*10*1000);
    setInterval(times_render, 10*1000);
    setInterval(leds_render, 60*1000);

    var client = mqtt.connect('ws://mqtt.home:1884/');

    client
        .on('message', mqtt_message)
        .subscribe('/calendar/all_events')
        .subscribe('/weather')
        .subscribe('/sensor/washingmachine/state')
        .subscribe('/sensor/tumbledryer/state')
        .subscribe('/location/+');
});
