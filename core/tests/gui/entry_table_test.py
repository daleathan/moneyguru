# Created By: Eric Mc Sween
# Created On: 2008-07-12
# Copyright 2010 Hardcoded Software (http://www.hardcoded.net)
# 
# This software is licensed under the "HS" License as described in the "LICENSE" file, 
# which should be included with this package. The terms are also available at 
# http://www.hardcoded.net/licenses/hs_license

from hsutil.testutil import eq_

from hscommon.currency import EUR
from hsutil.testutil import with_tmpdir, Patcher

from ...const import PaneType
from ...model.account import AccountType
from ..base import TestApp, with_app

#--- One account
def app_one_account():
    app = TestApp()
    app.add_account()
    app.mw.show_account()
    return app

def test_add_empty_entry_and_save():
    # An empty entry really gets saved.
    app = app_one_account()
    app.etable.add()
    app.etable.save_edits()
    app.drsel.select_prev_date_range()
    app.drsel.select_next_date_range()
    eq_(app.etable_count(), 1)

def test_add_twice_then_save():
    # Calling add() while in edition calls save_edits().
    # etable didn't have the same problem as ttable, but it did have this coverage missing
    # (commenting out the code didn't make tests fail)
    app = app_one_account()
    app.etable.add()
    app.etable.add()
    app.etable.save_edits()
    eq_(app.etable_count(), 2)

def test_delete_when_no_entry():
    # Don't crash when trying to remove a transaction from an empty list.
    app = app_one_account()
    app.etable.delete() # no crash

def test_selected_entry_index():
    # When there's no entry, the total row is selected
    app = app_one_account()
    eq_(app.etable.selected_indexes, [0])

def test_set_decrease_auto_decimal_place():
    # When the auto decimal place option is set, amounts in the decrease column are correctly set.
    app = app_one_account()
    app.app.auto_decimal_place = True
    app.add_entry(decrease='1234')
    eq_(app.etable[0].decrease, '12.34')

def test_set_increase_auto_decimal_place():
    # When the auto decimal place option is set, amounts in the increase column are correctly set.
    app = app_one_account()
    app.app.auto_decimal_place = True
    app.add_entry(increase='1234')
    eq_(app.etable[0].increase, '12.34')

def test_show_transfer_account_on_empty_row_does_nothing():
    # show_transfer_account() when the table is empty doesn't do anything
    app = app_one_account()
    app.etable.show_transfer_account() # no crash

@with_app(app_one_account)
def test_toggle_reconciliation(app):
    # Toggling reconciliation when no entry is selected doesn't cause a crash.
    app.aview.toggle_reconciliation_mode()
    app.etable.toggle_reconciled() # no crash

@with_app(app_one_account)
def test_total_line_balance_is_empty(app):
    # When there's no change in the balance, the balance cell of the total row shows nothing
    eq_(app.etable[0].balance, '')

#--- Three accounts
def app_three_accounts():
    app = TestApp()
    app.add_accounts('one', 'two', 'three') # three is the selected account (in second position)
    app.mw.show_account()
    return app

@with_app(app_three_accounts)
def test_add_transfer_entry(app):
    # Add a balancing entry to the account of the entry's transfer.
    app.add_entry(transfer='one', increase='42.00')
    app.mw.select_balance_sheet()
    app.bsheet.selected = app.bsheet.assets[0]
    app.bsheet.show_selected_account()
    eq_(app.etable_count(), 1)

#--- Liability account
def app_liability_account():
    app = TestApp()
    app.add_account(account_type=AccountType.Liability)
    app.mw.show_account()
    return app

#--- Income account
def app_income_account():
    app = TestApp()
    app.add_account(account_type=AccountType.Income)
    app.mw.show_account()
    return app

#--- Expense account
def app_expense_account():
    app = TestApp()
    app.add_account(account_type=AccountType.Expense)
    app.mw.show_account()
    return app

#--- Entry being added
def app_entry_being_added():
    app = TestApp()
    app.add_account()
    app.mw.show_account()
    app.etable.add()
    app.clear_gui_calls()
    return app

@with_app(app_entry_being_added)
def test_cancel_edits(app):
    # cancel_edits() calls view.refresh() and stop_editing()
    app.etable.cancel_edits()
    # We can't test the order of the gui calls, but stop_editing must happen first
    app.check_gui_calls(app.etable_gui, ['refresh', 'stop_editing'])

@with_app(app_entry_being_added)
def test_entry_is_added_before_total_line(app):
    # When adding an entry, never make it go after the total line
    eq_(app.etable.selected_index, 0)

@with_app(app_entry_being_added)
@with_tmpdir
def test_save(app, tmppath):
    # Saving the document ends the edition mode and save the edits
    filepath = unicode(tmppath + 'foo')
    app.doc.save_to_xml(filepath)
    app.check_gui_calls(app.etable_gui, ['stop_editing', 'refresh', 'show_selected_row'])
    assert app.etable.edited is None
    eq_(app.etable_count(), 1)

#--- One entry
def app_one_entry():
    app = TestApp()
    app.drsel.select_month_range()
    app.add_account('first')
    app.mw.show_account()
    app.add_entry('11/07/2008', 'description', 'payee', transfer='second', decrease='42')
    app.clear_gui_calls()
    return app

@with_app(app_one_entry)
def test_autofill_only_the_right_side(app):
    # When editing an attribute, only attributes to the right of it are autofilled
    app.etable.add()
    row = app.etable.selected_row
    row.payee = 'payee'
    eq_(row.description, '')

@with_app(app_one_entry)
def test_add_then_delete(app):
    # calling delete() while being in edition mode just cancels the current edit. it does *not*
    # delete the other entry as well.
    app.etable.add()
    app.etable.delete()
    eq_(app.etable_count(), 1)
    assert app.etable.edited is None

@with_app(app_one_entry)
def test_can_reconcile_expense(app):
    # income/expense entires can't be reconciled
    app.mw.select_income_statement()
    app.istatement.selected = app.istatement.expenses[0] # second
    app.istatement.show_selected_account()
    assert not app.etable[0].can_reconcile()

@with_app(app_one_entry)
def test_change_entry_gui_calls(app):
    # Changing an entry results in a refresh and a show_selected_row call
    row = app.etable[0]
    row.date = '12/07/2008'
    app.clear_gui_calls()
    app.etable.save_edits()
    app.check_gui_calls(app.etable_gui, ['refresh', 'show_selected_row'])

@with_app(app_one_entry)
def test_change_transfer(app):
    # Auto-creating an account refreshes the account tree.
    row = app.etable.selected_row
    row.transfer = 'Some new name'
    app.etable.save_edits()

@with_app(app_one_entry)
def test_debit_credit_columns(app):
    # when enabling the credit/debit columns option, increase/decrease columns are replaced with
    # credit/debit columns
    app.vopts.entry_table_debit_credit = True
    assert app.etable.columns.column_is_visible('debit')
    assert app.etable.columns.column_is_visible('credit')
    assert not app.etable.columns.column_is_visible('increase')
    assert not app.etable.columns.column_is_visible('decrease')
    eq_(app.etable[0].credit, '42.00')
    eq_(app.etable[0].debit, '')
    # credit/debit in total row works too
    eq_(app.etable.footer.credit, '42.00')

@with_app(app_one_entry)
def test_debit_credit_columns_edit(app):
    # editing a debit/credit columns work
    app.vopts.entry_table_debit_credit = True
    app.etable[0].debit = '43'
    app.etable.save_edits()
    app.vopts.entry_table_debit_credit = False
    eq_(app.etable[0].increase, '43.00')

@with_app(app_one_entry)
def test_delete_when_entry_selected(app):
    # Before deleting an entry, make sure the entry table is not in edition mode.
    app.etable.delete()
    app.check_gui_calls(app.etable_gui, ['stop_editing', 'refresh']) # Delete also refreshes.

@with_app(app_one_entry)
def test_duplicate_transaction(app):
    # duplicate_item() also works on the entry table.
    app.mainwindow.duplicate_item()
    eq_(app.etable_count(), 2)
    eq_(app.etable[0].description, 'description')
    # assume the rest is correct, torough tests in transaction_table_test

@with_app(app_one_entry)
def test_normal_row_is_not_bold(app):
    assert not app.etable[0].is_bold

@with_app(app_one_entry)
def test_set_invalid_amount(app):
    # setting an invalid amount reverts to the old amount
    app.etable[0].increase = 'foo' # no exception
    eq_(app.etable[0].increase, '')
    eq_(app.etable[0].decrease, '42.00')
    app.etable[0].decrease = 'foo' # no exception
    eq_(app.etable[0].increase, '')
    eq_(app.etable[0].decrease, '42.00')

@with_app(app_one_entry)
def test_set_invalid_reconciliation_date(app):
    # Setting an invalid reconciliation date, instead of causing an error, just sets the value
    # to None
    app.etable[0].reconciliation_date = 'invalid' # no crash
    eq_(app.etable[0].reconciliation_date, '')

@with_app(app_one_entry)
def test_show_transfer_account_entry_with_transfer_selected(app):
    # show_transfer_account() changes the shown account to 'second'
    app.etable.show_transfer_account()
    app.check_current_pane(PaneType.Account, account_name='second')
    # Previously, this was based on selected_account rather than shown_account
    assert not app.etable.columns.column_is_visible('balance')

@with_app(app_one_entry)
def test_show_transfer_account_then_add_entry(app):
    # When a new entry is created, it is created in the *shown* account, not the *selected*
    # account.
    app.etable.show_transfer_account()
    app.mainwindow.new_item()
    app.etable.save_edits()
    eq_(app.etable_count(), 2)

@with_app(app_one_entry)
def test_show_transfer_account_twice(app):
    # calling show_transfer_account() again brings the account view on 'first'
    app.etable.show_transfer_account()
    app.clear_gui_calls()
    app.etable.show_transfer_account()
    app.check_current_pane(PaneType.Account, account_name='first')

#--- Entry without transfer
def app_entry_without_transfer():
    app = TestApp()
    app.add_account('account')
    app.mw.show_account()
    app.add_entry(description='foobar', decrease='130')
    return app

@with_app(app_entry_without_transfer)
def test_entry_transfer(app):
    # Instead of showing 'Imbalance', the transfer column shows nothing.
    eq_(app.etable[0].transfer, '')

@with_app(app_entry_without_transfer)
def test_show_transfer_account_when_entry_has_no_transfer(app):
    # show_transfer_account() does nothing when an entry has no transfer
    app.etable.show_transfer_account() # no crash
    app.check_current_pane(PaneType.Account, account_name='account')

#--- Entry with decrease
def app_entry_with_decrease():
    app = TestApp()
    app.add_account()
    app.mw.show_account()
    app.add_entry(decrease='42.00')
    return app

@with_app(app_entry_with_decrease)
def test_set_decrease_to_zero_with_zero_increase(app):
    # Setting decrease to zero when the increase is already zero sets the amount to zero.
    row = app.etable.selected_row
    row.decrease = ''
    eq_(app.etable[0].decrease, '')

@with_app(app_entry_with_decrease)
def test_set_increase_to_zero_with_non_zero_decrease(app):
    # Setting increase to zero when the decrease being non-zero does nothing.
    row = app.etable.selected_row
    row.increase = ''
    eq_(app.etable[0].decrease, '42.00')

#--- Entry in liability
def app_entry_in_liability():
    app = TestApp()
    app.add_account('Credit card', account_type=AccountType.Liability)
    app.mw.show_account()
    app.add_entry('1/1/2008', 'Payment', increase='10')
    return app

#--- Transaction linked to numbered accounts
def app_txn_linked_to_numbered_accounts():
    app = TestApp()
    app.add_account('account1', account_number='4242')
    app.add_account('account2', account_number='4241')
    app.show_account('account1')
    # when entering the transactions, accounts are correctly found if their number is found
    app.add_entry(transfer='4241', decrease='42')
    return app

@with_app(app_txn_linked_to_numbered_accounts)
def test_transfer_column(app):
    # When an account is numbered, the from and to column display those numbers with the name.
    eq_(app.etable[0].transfer, '4241 - account2')

#--- EUR account with EUR entries
def app_eur_account_with_eur_entries():
    app = TestApp()
    app.add_account(currency=EUR)
    app.mw.show_account()
    app.add_entry(increase='42') # EUR
    app.add_entry(decrease='42') # EUR
    return app

@with_app(app_eur_account_with_eur_entries)
def test_amounts_display(app):
    # The amounts' currency are explicitly displayed.
    eq_(app.etable[0].increase, 'EUR 42.00')
    eq_(app.etable[0].balance, 'EUR 42.00')
    eq_(app.etable[1].decrease, 'EUR 42.00')
    eq_(app.etable[1].balance, 'EUR 0.00')

#--- Two entries
def app_two_entries():
    app = TestApp()
    app.add_account()
    app.mw.show_account()
    app.add_entry('11/07/2008', 'first', increase='42')
    app.add_entry('12/07/2008', 'second', decrease='12')
    app.clear_gui_calls()
    return app

@with_app(app_two_entries)
def test_remove_entry_through_tpanel(app):
    # Removing an entry through tpanel (by unassigning the split from the shown account) correctly
    # updates selection at the document level
    app.mw.edit_item()
    # We're not too sure which split is assigned to the account, so we unassign both
    app.stable[0].account = ''
    app.stable.save_edits()
    app.stable[1].account = ''
    app.stable.save_edits()
    app.tpanel.save()
    app.mw.edit_item() # Because doc selection has been updated, the first entry is shown in tpanel.
    eq_(app.tpanel.description, 'first')

@with_app(app_two_entries)
def test_search(app):
    # Searching when on etable doesn't switch to the ttable, and shows the results in etable
    app.sfield.query = 'second'
    app.check_gui_calls_partial(app.mainwindow_gui, not_expected=['show_transaction_table'])
    eq_(app.etable_count(), 1)
    eq_(app.etable[0].description, 'second')

@with_app(app_two_entries)
def test_selection(app):
    # EntryTable stays in sync with TransactionTable.
    app.mw.select_transaction_table()
    app.ttable.select([0])
    app.clear_gui_calls()
    app.mw.select_balance_sheet()
    app.bsheet.selected = app.bsheet.assets[0]
    app.bsheet.show_selected_account()
    eq_(app.etable.selected_indexes, [0])
    app.check_gui_calls(app.etable_gui, ['refresh', 'show_selected_row'])

@with_app(app_two_entries)
def test_total_row(app):
    # The total row shows total increase and decrease with the date being the last day of the date
    # range. The balance column shows balance delta.
    row = app.etable[2]
    eq_(row.date, '31/12/2008')
    eq_(row.description, 'TOTAL')
    eq_(row.increase, '42.00')
    eq_(row.decrease, '12.00')
    eq_(row.balance, '+30.00')
    assert row.is_bold

#--- Entry in previous range
def app_entry_in_previous_range():
    app = TestApp()
    app.drsel.select_month_range()
    app.add_account()
    app.mw.show_account()
    app.add_entry('11/06/2008', 'first')
    app.add_entry('11/07/2008', 'second')
    return app

@with_app(app_entry_in_previous_range)
def test_previous_balance_row_is_bold(app):
    assert app.etable[0].is_bold

@with_app(app_entry_in_previous_range)
def test_selection_after_date_range_change(app):
    # The selection in the document is correctly updated when the date range changes.
    # The tpanel loads the document selection, so this is why we test through it.
    app.drsel.select_prev_date_range()
    app.tpanel.load()
    eq_(app.tpanel.description, 'first')

#--- Two entries in two accounts
def app_two_entries_in_two_accounts():
    app = TestApp()
    app.add_account()
    app.mw.show_account()
    app.add_entry('11/07/2008', 'first')
    app.add_account()
    app.mw.show_account()
    app.add_entry('12/07/2008', 'second')
    return app

@with_app(app_two_entries_in_two_accounts)
def test_selection_after_connect(app):
    # The selection in the document is correctly updated when the selected account changes.
    # The tpanel loads the document selection, so this is why we test through it.
    app.mw.select_transaction_table()
    app.ttable.select([0]) # first
    app.mw.select_balance_sheet()
    app.bsheet.selected = app.bsheet.assets[1]
    app.bsheet.show_selected_account()
    app.tpanel.load()
    eq_(app.tpanel.description, 'second')

#--- Two entries with one reconciled
def app_two_entries_with_one_reconciled():
    app = TestApp()
    app.add_account()
    app.mw.show_account()
    app.add_entry(increase='1')
    app.add_entry(increase='2')
    app.aview.toggle_reconciliation_mode()
    app.etable[0].toggle_reconciled()
    return app

@with_app(app_two_entries_with_one_reconciled)
def test_reconciled(app):
    # The first entry has been reconciled and its pending status is the same as its reconciled
    # status.
    assert app.etable[0].reconciled

@with_app(app_two_entries_with_one_reconciled)
def test_toggle_both(app):
    # When reconciling two entries at once, as soon as one of the entries is not reconciled, the
    # new value is True
    app.etable.select([0, 1])
    app.etable.toggle_reconciled()
    assert app.etable[0].reconciled # haven't been touched
    assert app.etable[1].reconciled

@with_app(app_two_entries_with_one_reconciled)
def test_toggle_both_twice(app):
    # reconciled entries can be unreconciled through toggle_reconciled().
    app.etable.select([0, 1])
    app.etable.toggle_reconciled()
    app.etable.toggle_reconciled() # now, both entries are unreconciled
    assert not app.etable[0].reconciled
    assert not app.etable[1].reconciled

#--- Two entries in two currencies
def app_two_entries_two_currencies():
    app = TestApp()
    app.add_account()
    app.mw.show_account()
    app.add_entry(increase='1')
    app.add_entry(increase='2 cad')
    return app

@with_app(app_two_entries_two_currencies)
def test_can_reconcile(app):
    # an entry with a foreign currency can't be reconciled.
    app.aview.toggle_reconciliation_mode()
    assert not app.etable[1].can_reconcile()

@with_app(app_two_entries_two_currencies)
def test_toggle_reconcilitation_on_both(app):
    # When both entries are selected and toggle_reconciliation is called, only the first one
    # is toggled.
    app.aview.toggle_reconciliation_mode()
    app.etable.select([0, 1])
    app.etable.toggle_reconciled()
    assert app.etable[0].reconciled
    assert not app.etable[1].reconciled

#--- Three entries different dates
def app_three_entries_different_dates():
    app = TestApp()
    app.add_account()
    app.mw.show_account()
    app.add_entry('01/08/2008')
    app.add_entry('02/08/2008')
    # The date has to be "further" so select_nearest_date() doesn't pick it
    app.add_entry('04/08/2008')
    return app

@with_app(app_three_entries_different_dates)
def test_delete_second_entry(app):
    # When deleting the second entry, the entry after it ends up selected.
    app.etable.select([1])
    app.etable.delete()
    eq_(app.etable.selected_indexes, [1])

#--- Split transaction
def app_split_transaction():
    app = TestApp()
    app.add_account('first')
    app.mw.show_account()
    app.add_entry('08/11/2008', description='foobar', transfer='second', increase='42')
    app.tpanel.load()
    app.stable.add()
    app.stable.selected_row.account = 'third'
    app.stable.selected_row.debit = '20'
    app.stable.save_edits()
    app.tpanel.save()
    return app
    
def test_autofill():
    # when the entry is part of a split, don't autofill the transfer
    app = app_split_transaction()
    app.etable.add()
    app.etable.edited.description = 'foobar'
    eq_(app.etable.edited.transfer, '')

@with_app(app_split_transaction)
def test_dont_allow_amount_change_for_splits(app):
    # Amount of entries belonging to splits can't be set.
    assert not app.etable[0].can_edit_cell('increase')
    assert not app.etable[0].can_edit_cell('decrease')

def test_show_transfer_account():
    # show_transfer_account() cycles through all splits of the entry
    app = app_split_transaction()
    app.etable.show_transfer_account()
    app.check_current_pane(PaneType.Account, account_name='second')
    app.etable.show_transfer_account()
    app.check_current_pane(PaneType.Account, account_name='third')
    app.etable.show_transfer_account()
    app.check_current_pane(PaneType.Account, account_name='first')

def test_show_transfer_account_with_unassigned_split():
    # If there's an unassigned split among the splits, just skip over it
    app = app_split_transaction()
    app.mainwindow.edit_item()
    app.stable.select([1]) # second
    app.stable.selected_row.account = ''
    app.stable.save_edits()
    app.tpanel.save()
    app.etable.show_transfer_account() # skip unassigned, and to to third
    app.check_current_pane(PaneType.Account, account_name='third')

#--- Two splits same account
def app_two_splits_same_account():
    app = TestApp()
    app.add_account('first')
    app.mw.show_account()
    app.add_entry('08/11/2008', description='foobar', transfer='second', increase='42')
    app.tpanel.load()
    app.stable.select([0])
    app.stable.selected_row.debit = '20'
    app.stable.save_edits()
    app.stable.select([2])
    app.stable.selected_row.account = 'first'
    app.stable.save_edits()
    app.tpanel.save()
    return app

@with_app(app_two_splits_same_account)
def test_delete_both_entries(app):
    # There would be a crash when deleting two entries belonging to the same txn
    app.etable.select([0, 1])
    app.etable.delete() # no crash
    eq_(app.etable_count(), 0)

#--- With budget
def app_with_budget():
    app = TestApp()
    p = Patcher()
    p.patch_today(2008, 1, 27)
    app.drsel.select_today_date_range()
    app.add_account('foo', account_type=AccountType.Expense)
    app.add_budget('foo', None, '100')
    app.show_account('foo')
    return app, p

@with_app(app_with_budget)
def test_budget_spawns(app):
    # When a budget is set budget transaction spawns show up in wtable, at the end of each month.
    eq_(app.etable_count(), 12)
    assert app.etable[0].is_budget
    # Budget spawns can't be edited
    assert not app.etable.can_edit_cell('date', 0)

#--- Unreconciled entry in the middle of two reconciled entries
def app_unreconciled_between_two_reconciled():
    app = TestApp()
    app.add_account()
    app.mw.show_account()
    app.add_entry('01/07/2010', description='one', reconciliation_date='01/07/2010')
    app.add_entry('02/07/2010', description='two')
    app.add_entry('03/07/2010', description='three', reconciliation_date='02/07/2010')
    return app

@with_app(app_unreconciled_between_two_reconciled)
def test_sort_by_reconciliation_date_with_unreconciled_in_middle(app):
    # When an entry is not reconciled, the reconciliation date sorting order falls back on entry
    # date.
    app.etable.sort_by('reconciliation_date')
    eq_(app.etable[0].description, 'one')
    eq_(app.etable[1].description, 'two')
    eq_(app.etable[2].description, 'three')

#--- Generators
def test_amount_of_selected_entry():
    def check(app, expected_increase, expected_decrease):
        eq_(app.etable.selected_row.increase, expected_increase)
        eq_(app.etable.selected_row.decrease, expected_decrease)
    
    # The amount correctly stays in the decrease column
    app = app_entry_with_decrease()
    yield check, app, '', '42.00'
    
    # The amount correctly stays in the increase column, even though it's a credit
    app = app_entry_in_liability()
    yield check, app, '10.00', ''

def test_should_show_balance_column():
    def check(app, expected):
        eq_(app.etable.columns.column_is_visible('balance'), expected)
    
    # When a liability account is selected, we show the balance column.
    app = app_liability_account()
    yield check, app, True
    
    # When an income account is selected, we don't show the balance column.
    app = app_income_account()
    yield check, app, False
    
    # When an expense account is selected, we don't show the balance column.
    app = app_expense_account()
    yield check, app, False
    
    # When an asset account is selected, we show the balance column.
    app = app_one_account()
    yield check, app, True
