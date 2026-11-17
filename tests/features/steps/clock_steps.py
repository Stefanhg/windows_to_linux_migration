from behave import then
from desktop import cinnamon, eventually


@then('both taskbars render their current clock text')
def clock_visible(context):
    def rendered():
        clocks = cinnamon('''
            return imports.ui.appletManager.getRunningInstancesForUuid('calendar@cinnamon.org')
                .map(a=>({monitor:a.panel.monitorIndex,visible:a.actor.visible,
                    mapped:a.actor.mapped,width:a.actor.width,labelVisible:a._applet_label.visible,
                    text:a._applet_label.get_text(),expected:a.clock.get_clock()}));
        ''')
        return all(any(c['monitor'] == monitor and c['visible'] and c['mapped'] and c['width'] > 0
                       and c['labelVisible'] and c['text'].strip() and c['text'] == c['expected']
                       for c in clocks) for monitor in (0, 1))
    eventually(rendered, 'visible clock text on both live taskbars')
