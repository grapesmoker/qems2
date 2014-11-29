function add_row_to_cat_table() {
    var current_forms = parseInt($('#id_distentry-INITIAL_FORMS')[0].value);
    var next_form = current_forms + 1;
    $('#dist-table > tbody > tr:last').
    after(sprintf(
        '<tr><td><input id="id_distentry-%d-category" width="100" type="text" name="categories" maxlength="100" /></td> \
<td><input id="id_distentry-%d-subcategory" type="text" name="subcategories" maxlength="100" /></td> \
<td><input id="id_distentry-%d-num_tossups" width="10" type="text" class="spinner" name="num_tossups" /></td> \
<td><input id="id_distentry-%d-num_bonuses" width="10" type="text" class="spinner" name="num_bonuses" /></td> \
<td><input id="id_distentry-%d-fin_tossups" width="10" type="text" class="spinner" name="fin_tossups" /></td> \
<td><input id="id_distentry-%d-fin_bonuses" width="10" type="text" class="spinner" name="fin_bonuses" /></td> \
<td>&nbsp;</td></tr>', next_form, next_form, next_form, next_form, next_form, next_form));
    
    $('.spinner').width(10).spinner({'min': 0})
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

    try {
        var tu_text_quill = new Quill('#tossup-editor', {
            formats: ['bold', 'italic', 'underline']
        });
        var tu_ans_quill = new Quill('#answer-editor', {
            formats: ['bold', 'italic', 'underline']
        });

        tu_text_quill.addModule('toolbar', {container: '#toolbar'})
        tu_ans_quill.addModule('toolbar', {container: '#toolbar'})

        $('#submit-tossup').click(function(e) {
            // e.preventDefault();
            var tu_text = $(tu_text_quill.getHTML()).html();
            var tu_ans = $(tu_ans_quill.getHTML()).html();
            $('#id_tossup_text').val(tu_text);
            $('#id_tossup_answer').val(tu_ans);
        })
    }
    catch (error) {
        console.log(error);
    }

    try {

        var bs_leadin_quill = new Quill('#bonus-leadin', {
            formats: ['bold', 'italic', 'underline']
        });

        var bs_part1_quill = new Quill('#part-1-text', {
            formats: ['bold', 'italic', 'underline']
        })

        var bs_ans1_quill = new Quill('#part-1-answer', {
            formats: ['bold', 'italic', 'underline']
        })

        var bs_part2_quill = new Quill('#part-2-text', {
            formats: ['bold', 'italic', 'underline']
        })

        var bs_ans2_quill = new Quill('#part-2-answer', {
            formats: ['bold', 'italic', 'underline']
        })

        var bs_part3_quill = new Quill('#part-3-text', {
            formats: ['bold', 'italic', 'underline']
        })

        var bs_ans3_quill = new Quill('#part-3-answer', {
            formats: ['bold', 'italic', 'underline']
        })

        bs_leadin_quill.addModule('toolbar', {container: '#toolbar'})
        bs_part1_quill.addModule('toolbar', {container: '#toolbar'})
        bs_ans1_quill.addModule('toolbar', {container: '#toolbar'})
        bs_part2_quill.addModule('toolbar', {container: '#toolbar'})

        bs_ans2_quill.addModule('toolbar', {container: '#toolbar'})
        bs_part3_quill.addModule('toolbar', {container: '#toolbar'})
        bs_ans3_quill.addModule('toolbar', {container: '#toolbar'})

        $('#submit-bonus').click(function(e) {
            //e.preventDefault();

            var bs_leadin = $(bs_leadin_quill.getHTML()).html();
            var bs_part1_text = $(bs_part1_quill.getHTML()).html();
            var bs_ans1_text = $(bs_ans1_quill.getHTML()).html();
            var bs_part2_text = $(bs_part2_quill.getHTML()).html();
            var bs_ans2_text = $(bs_ans2_quill.getHTML()).html();
            var bs_part3_text = $(bs_part3_quill.getHTML()).html();
            var bs_ans3_text = $(bs_ans3_quill.getHTML()).html();

            // console.log($(bs_leadin_quill.getHTML()))

            $('#id_leadin').val(bs_leadin);
            $('#id_part1_text').val(bs_part1_text);
            $('#id_part1_answer').val(bs_ans1_text);
            $('#id_part2_text').val(bs_part2_text);
            $('#id_part2_answer').val(bs_ans2_text);
            $('#id_part3_text').val(bs_part3_text);
            $('#id_part3_answer').val(bs_ans3_text);
        })
    }
    catch (error) {
        console.log(error);
    }

    // Set up sorting for all tables
    $('#tu-status-table').tablesorter();
    $('#editors-table').tablesorter();
    $('#writers-table').tablesorter();    
    $('#set-wide-reqs-table').tablesorter();
    $('#tb-reqs-table').tablesorter();
    $('#packets-table').tablesorter();
    $('#category-tossup-table').tablesorter();
    $('#category-bonus-table').tablesorter();
    $('#question-set-table').tablesorter();
    $('#distributions-table').tablesorter();

    $('#tossup-table').tablesorter().tablesorterPager({container: $("#tossup-pager")});
    $('#tossup-pager').css({cursor: "pointer", position: "relative", top: "0px"});

    $('#bonus-table').tablesorter().tablesorterPager({container: $("#bonus-pager")});
    $('#bonus-pager').css({cursor: "pointer", position: "relative", top: "0px"});

    /*tinymce.init({
        selector: 'textarea.question_text',
        menubar: false,
        toolbar: 'undo redo | bold italic underline',
        fontsize_formats: '12px 14px 16px',
        setup: function(ed) {
            ed.on('init', function() {
                this.getDoc().body.style.fontSize = '18px';

                // Needed so that what we write to the text area isn't overwritten
                this.settings.add_form_submit_trigger = false;
                this.on('submit', function (ed, e) {
                    var jqueryId = "#" + this.id;
                    $(jqueryId).val($(this.getBody()).html());
                });
            });
        },
        width: 900,
        /*formats: {
            underline: {inline: 'u', exact: true},
            italic: {inline: 'i', exact: true},
            bold: {inline: 'b', exact: true}
        }
    });*/
    
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
    
    $(document).tooltip();
    
    $('.spinner').width(25).spinner({'min': 0})
    $('#add-row').click(add_row_to_cat_table)

    $('.delete_tossup').click(function(e) {
        e.preventDefault();
        var result = confirm("You are about to delete this tossup! If you do so, you will not be able to recover it! Are you ABSOLUTELY SURE you want to do that?!");
        if (result == true) {
            $.post('/delete_tossup/', {tossup_id: $(this).attr('value')}, function (response) {
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

    $('.delete_bonus').click(function(e) {
        e.preventDefault();
        var result = confirm("You are about to delete this bonus! If you do so, you will not be able to recover it! Are you ABSOLUTELY SURE you want to do that?!");
        if (result == true) {
            $.post('/delete_bonus/', {bonus_id: $(this).attr('value')}, function (response) {
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
