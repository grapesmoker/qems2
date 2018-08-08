$(function () {

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

    /* to be deprecated
    // Set up adding rows on /edit_distribution/
    $('#add-rows').click(function() {
        var current = parseInt($('#id_distentry-INITIAL_FORMS')[0].value),
            next = current + 1;
        $('#distribution-table tbody > tr:last').clone(true).insertAfter('#distribution-table tbody > tr:last');
        $('#distribution-table tbody > tr:last input').each(function() {
            var current_id = $(this).attr('id');
            $(this).attr('id', current_id.replace(current, next));
        });
        //var num_rows = $('#num-rows').val();
        //add_rows();
    });*/

    // Set up sorting for all tables w/ tablesorter class
    $('table.tablesorter').tablesorter({
        widthFixed:true
    });

    // Make columns of some tables the same width
    function match_table(source,dest) {
        var cols = [];
        $(source).find('th').each(function() {
            cols.push($(this).width());
        });
        cols.reverse();
        $(dest).find('th').each(function() {
            $(this).width(cols.pop());
        });
    }

    match_table('#tossup-table','#bonus-table');
    match_table('#category-tossup-table','#category-bonus-table');
    match_table('#packet-tossup-table','#packet-bonus-table');
    match_table('#bulk-change-tossup-table','#bulk-change-bonus-table');

    // $("#tossup-table").trigger("destroy", [false, function(){
    //     $('#tossup-table').tablesorter({
    //         dateFormat : "mmddyyyy",
    //         headers: { 
    //             6: { sorter: 'shortDate'},
    //             7: { sorter: 'shortDate'}
    //         }
    //     });
    // }]);
    // 
    // 
    // $("#comments-table").trigger("destroy", [false, function(){
    //     $('#comments-table').tablesorter({
    //         dateFormat : "mmddyyyy",
    //         headers: { 
    //             3: { sorter: 'shortDate'}
    //         }
    //     });
    // }]);


    //$('#comments-table').tablesorter({
    //    headers: { 3: { sorter: 'shortDate'} }
    //});

    
    // $('#tossup-pager').css({cursor: "pointer", position: "relative", top: "0px"});

    // $('#bonus-table').tablesorter().tablesorterPager({container: $("#bonus-pager")});
    // $('#bonus-pager').css({cursor: "pointer", position: "relative", top: "0px"});

    // Set up autofocus on /type_questions/ & /add_tossups/
    $('form#type-questions #id_questions').focus();
    $('form#add-tossups #id_tossup_text').focus();

    // Open all
    $('.button.open-all').click(function() {
        var selector = _.rest($(this).attr('class').split(/\s+/), 3);
        console.log(selector);
        var links = [];

        _.each(selector, function(element, index, list) {
            $("table[id*='" + element + "'] a").each(function() {
                links.push($(this).attr('href'));
            });
        });
        _.each(_.uniq(links), function(element, index, list) {
            window.open(element);
        });
    });

    /*$('#id_player_to_add').autocomplete({
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
    })*/

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
            var qset_id = $(this).attr('qset-id');
            $.post('/delete_packet/', {packet_id: $(this).attr('value')}, function (response) {
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

    $('.delete_writer').click(function(e) {
        e.preventDefault();
        var result = confirm("You are about to remove this writer from the set! Are you sure that you want to do that?");
        if (result == true) {
            var qset_id = $(this).attr('qset-id');
            $.post('/delete_writer/', {writer_id: $(this).attr('value'), qset_id: $(this).attr('qset-id')}, function (response) {
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

    $('.delete_editor').click(function(e) {
        e.preventDefault();
        var result = confirm("You are about to remove this editor from the set! Are you sure you want to do that?");
        if (result == true) {
            var qset_id = $(this).attr('qset-id');
            $.post('/delete_editor/', {editor_id: $(this).attr('value'), qset_id: $(this).attr('qset-id')}, function (response) {
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

    $('.delete_all_comments').click(function (e) {
        e.preventDefault();
        var result = confirm("Are you sure you want to delete all comments?  It can only be restored by a QEMS2 admin.");
        if (result == true) {
            $.post('/delete_all_comments/', { question_id: $(this).attr('value'), qset_id: $(this).attr('qset'), question_type: $(this).attr('question-type'), }, function (response) {
                var json_response = $.parseJSON(response);
                var dialog = $('#info-dialog').dialog({
                    modal: true,
                    buttons: {
                        Ok: function () {
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
    
    $('.delete_set').click(function(e) {
        e.preventDefault();
        var result = confirm("Are you sure you want to delete this question set?");
        if (result == true) {
            var result2 = confirm("Seriously, you really want to delete this question set?");
            if (result2 == true) {
                $.post('/delete_set/', {qset_id: $(this).attr('value')}, function (response) {
                    var json_response = $.parseJSON(response);
                    var dialog = $('#info-dialog').dialog({
                        modal: true,
                        buttons: {
                            Ok: function() {
                                $(this).dialog('close');
                                window.location.replace('/main/');
                            }
                        }
                    })
                    dialog.append('<div class="' + json_response['message_class'] + '">' + json_response['message'] + '</div>');
                    dialog.dialog('open');
                });
            }
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
