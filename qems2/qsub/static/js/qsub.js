function add_row_to_cat_table() {
    var current_forms = parseInt($('#id_distentry-INITIAL_FORMS')[0].value);
    var next_form = current_forms + 1;
    $('#dist-table > tbody > tr:last').
    after(sprintf(
        '<tr><td><input id="id_distentry-%d-category" width="100" type="text" name="categories" maxlength="100" /></td> \
<td><input id="id_distentry-%d-subcategory" type="text" name="subcategories" maxlength="100" /></td> \
<td><input id="id_distentry-%d-num_tossups" type="number" min="0" step="1"class="spinner" name="num_tossups" /></td> \
<td><input id="id_distentry-%d-num_bonuses" type="number" min="0" step="1"class="spinner" name="num_bonuses" /></td> \
<td><input id="id_distentry-%d-fin_tossups" type="number" min="0" step="1"class="spinner" name="fin_tossups" /></td> \
<td><input id="id_distentry-%d-fin_bonuses" type="number" min="0" step="1" class="spinner" name="fin_bonuses" /></td> \
<td>&nbsp;</td></tr>', next_form, next_form, next_form, next_form, next_form, next_form));
}

function make_table_same(source,dest) {
    var cols = [];
    $(source).find('th').each(function() {
        cols.push($(this).width());
    });
    cols.reverse();
    $(dest).find('th').each(function() {
        $(this).width(cols.pop());
    });
}

$.browser = {}

$(function () {

    $.browser.msie = false;
    /*$.browser.version = 0;
    if (navigator.userAgent.match(/MSIE ([0-9]+)\./)) {
        jQuery.browser.msie = true;
        jQuery.browser.version = RegExp.$1;
    }*/

    var csrftoken = $.cookie('csrftoken');

    function csrfSafeMethod(method) {
        // these HTTP methods do not require CSRF protection
        return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
    }

    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
            if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            }
        }
    });

    // Set up sorting for all tables
    $('#set-status-table').tablesorter();
    $('#editors-table').tablesorter();
    $('#writers-table').tablesorter();
    $('#set-wide-reqs-table').tablesorter();
    $('#tb-reqs-table').tablesorter();
    $('#packets-table').tablesorter();
    $('#category-tossup-table').tablesorter({widthFixed:true});
    $('#category-bonus-table').tablesorter({widthFixed:true});
    $('#qsets-write-table').tablesorter();
    $('#qsets-edit-table').tablesorter();
    $('#qsets-owned-table').tablesorter();
    $('#distributions-table').tablesorter();
    $('#writer-stats-table').tablesorter();
    $('#packet-tossup-table').tablesorter({widthFixed:true});
    $('#packet-bonus-table').tablesorter({widthFixed:true});
    $('#packet-status-tossup-table').tablesorter();
    $('#packet-status-bonus-table').tablesorter();
    $('#tossup-table').tablesorter({widthFixed:true});
    $('#bonus-table').tablesorter({widthFixed:true});
    $('#bulk-change-tossup-table').tablesorter();
    $('#bulk-change-bonus-table').tablesorter();

    // Make columns of some tables the same width
    make_table_same('#tossup-table','#bonus-table');
    make_table_same('#category-tossup-table','#category-bonus-table');
    make_table_same('#packet-tossup-table','#packet-bonus-table');
    // $('#tossup-table').tablesorter().tablesorterPager({container: $("#tossup-pager")});
    // $('#tossup-pager').css({cursor: "pointer", position: "relative", top: "0px"});

    // $('#bonus-table').tablesorter().tablesorterPager({container: $("#bonus-pager")});
    // $('#bonus-pager').css({cursor: "pointer", position: "relative", top: "0px"});

    $('#id_player_to_add').autocomplete({
    source: "/find_player/?tour_id=" + $('#tour_id').val() + $(this).val(),
    select: function(event, ui) {
        $('#id_player_to_add').val(ui.item.label);
        $('#id_hd_player_to_add').val(ui.item.value);

        return false;
    }
    }),

    $('#id_teammate_to_add').autocomplete({
    source: "/find_teammate/?team_id=" + $('#team_id').val() + $(this).val(),
    select: function(event, ui) {
        $('#id_teammate_to_add').val(ui.item.label);
        $('#id_hd_teammate_to_add').val(ui.item.value);

        return false;
    }
    })

    $('#add-row').click(add_row_to_cat_table)

    $('.delete_tossup').click(function(e) {
        e.preventDefault();
        var result = confirm("You are about to delete this tossup! If you do so, you will not be able to recover it! Are you ABSOLUTELY SURE you want to do that?!");
        if (result == true) {
            var qset_id = $(this).attr('qset-id');
            $.post('/delete_tossup/', {tossup_id: $(this).attr('value')}, function (response) {
                var json_response = $.parseJSON(response);
                var dialog = $('#info-dialog').dialog({
                    modal: true,
                    buttons: {
                        Ok: function() {
                            $(this).dialog('close');
                            window.location.replace('/edit_question_set/' + qset_id);
                        }
                    }
                })
                dialog.append('<div class="' + json_response['message_class'] + '">' + json_response['message'] + '</div>');
                dialog.dialog('open');
            });
        }
    });

    $('.delete_bonus').click(function(e) {
        e.preventDefault();
        var result = confirm("You are about to delete this bonus! If you do so, you will not be able to recover it! Are you ABSOLUTELY SURE you want to do that?!");
        if (result == true) {
            var qset_id = $(this).attr('qset-id');            
            $.post('/delete_bonus/', {bonus_id: $(this).attr('value')}, function (response) {
                var json_response = $.parseJSON(response);
                var dialog = $('#info-dialog').dialog({
                    modal: true,
                    buttons: {
                        Ok: function() {
                            $(this).dialog('close');
                            window.location.replace('/edit_question_set/' + qset_id);
                        }
                    }
                })
                dialog.append('<div class="' + json_response['message_class'] + '">' + json_response['message'] + '</div>');
                dialog.dialog('open');
            });
        }
    });

    $('.delete_packet').click(function(e) {
        e.preventDefault();
        var result = confirm("You are about to delete this packet! If you do so, you will not be able to recover it! 99% of the time this is a terrible idea and you should not do it! Are you ABSOLUTELY SURE you want to do that?!");
        if (result == true) {
            $.post('/delete_packet/', {packet_id: $(this).attr('value')}, function (response) {
                var json_response = $.parseJSON(response);
                var dialog = $('#info-dialog').dialog({
                    modal: true,
                    buttons: {
                        Ok: function() {
                            $(this).dialog('close');
                            window.location.replace('/edit_question_set/' + $('#qset-id').val());
                        }
                    }
                })
                dialog.append('<div class="' + json_response['message_class'] + '">' + json_response['message'] + '</div>');
                dialog.dialog('open');
            });
        }
    });

    $('.delete_writer').click(function(e) {
        e.preventDefault();
        var result = confirm("You are about to remove this writer from the set! Are you sure that you want to do that?");
        if (result == true) {
            $.post('/delete_writer/', {writer_id: $(this).attr('value'), qset_id: $('#qset-id').val()}, function (response) {
                var json_response = $.parseJSON(response);
                var dialog = $('#info-dialog').dialog({
                    modal: true,
                    buttons: {
                        Ok: function() {
                            $(this).dialog('close');
                            window.location.replace('/edit_question_set/' + $('#qset-id').val());
                        }
                    }
                })
                dialog.append('<div class="' + json_response['message_class'] + '">' + json_response['message'] + '</div>');
                dialog.dialog('open');
            });
        }
    });

    $('.delete_editor').click(function(e) {
        e.preventDefault();
        var result = confirm("You are about to remove this editor from the set! Are you sure you want to do that?");
        if (result == true) {
            $.post('/delete_editor/', {editor_id: $(this).attr('value'), qset_id: $('#qset-id').val()}, function (response) {
                var json_response = $.parseJSON(response);
                var dialog = $('#info-dialog').dialog({
                    modal: true,
                    buttons: {
                        Ok: function() {
                            $(this).dialog('close');
                            window.location.replace('/edit_question_set/' + $('#qset-id').val());
                        }
                    }
                })
                dialog.append('<div class="' + json_response['message_class'] + '">' + json_response['message'] + '</div>');
                dialog.dialog('open');
            });
        }
    });

    $('.delete_comment').click(function(e) {
        e.preventDefault();        
        var result = confirm("Are you sure you want to delete this comment?  It can only be restored by a QEMS2 admin.");
        if (result == true) {
            $.post('/delete_comment/', {comment_id: $(this).attr('value'), qset_id: $(this).attr('qset')}, function (response) {
                var json_response = $.parseJSON(response);
                var dialog = $('#info-dialog').dialog({
                    modal: true,
                    buttons: {
                        Ok: function() {
                            $(this).dialog('close');
                            window.location.reload();
                        }
                    }
                })
                dialog.append('<div class="' + json_response['message_class'] + '">' + json_response['message'] + '</div>');
                dialog.dialog('open');
            });
        }
    });

    $('.restore_tossup').click(function(e) {
        e.preventDefault();
        var result = confirm("Are you sure that you want to restore this question to this version?");
        if (result == true) {
            $.post('/restore_tossup/', {th_id: $(this).attr('value'), qset_id: $(this).attr('qset')}, function (response) {
                var json_response = $.parseJSON(response);
                var dialog = $('#info-dialog').dialog({
                    modal: true,
                    buttons: {
                        Ok: function() {
                            $(this).dialog('close');
                            window.location.reload();
                        }
                    }
                })
                dialog.append('<div class="' + json_response['message_class'] + '">' + json_response['message'] + '</div>');
                dialog.dialog('open');
            });
        }
    });

    $('.restore_bonus').click(function(e) {
        e.preventDefault();
        var result = confirm("Are you sure that you want to restore this question to this version?");
        if (result == true) {
            $.post('/restore_bonus/', {bh_id: $(this).attr('value'), qset_id: $(this).attr('qset')}, function (response) {
                var json_response = $.parseJSON(response);
                var dialog = $('#info-dialog').dialog({
                    modal: true,
                    buttons: {
                        Ok: function() {
                            $(this).dialog('close');
                            window.location.reload();
                        }
                    }
                })
                dialog.append('<div class="' + json_response['message_class'] + '">' + json_response['message'] + '</div>');
                dialog.dialog('open');
            });
        }
    });

    $('.convert_tossup').click(function(e) {
        e.preventDefault();
        var result = confirm("Are you sure that you want to change this tossup's type?");
        if (result == true) {
            var qset_id = $(this).attr('qset-id');            
            $.post('/convert_tossup/', { tossup_id: $(this).attr('value'), qset_id: $(this).attr('qset-id'), target_type: $(this).attr('target-type')}, function (response) {
                var json_response = $.parseJSON(response);
                var dialog = $('#info-dialog').dialog({
                    modal: true,
                    buttons: {
                        Ok: function() {
                            $(this).dialog('close');
                            window.location.replace('/edit_question_set/' + qset_id);
                        }
                    }
                })
                dialog.append('<div class="' + json_response['message_class'] + '">' + json_response['message'] + '</div>');
                dialog.dialog('open');
            });
        }
    });

    $('.convert_bonus').click(function(e) {
        e.preventDefault();
        var result = confirm("Are you sure that you want to change this bonus' type?");
        if (result == true) {
            var qset_id = $(this).attr('qset-id');                        
            $.post('/convert_bonus/', {bonus_id: $(this).attr('value'), qset_id: $(this).attr('qset-id'), target_type: $(this).attr('target-type')}, function (response) {
                var json_response = $.parseJSON(response);
                var dialog = $('#info-dialog').dialog({
                    modal: true,
                    buttons: {
                        Ok: function() {
                            $(this).dialog('close');
                            window.location.replace('/edit_question_set/' + qset_id);
                        }
                    }
                })
                dialog.append('<div class="' + json_response['message_class'] + '">' + json_response['message'] + '</div>');
                dialog.dialog('open');
            });
        }
    });

    $('#upload-dialog').dialog({
        autoOpen: false,
        width: 600,
        height: 400,
        buttons: {
            Cancel: function() {
                $(this).dialog('close');
            },
            Ok: function() {
                $(this).find('form').submit();
            }
        }
    })

    $('#upload-questions').click(function () {
        $('#upload-dialog').dialog('open');
    })
});
