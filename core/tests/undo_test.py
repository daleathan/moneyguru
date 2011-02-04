# Created By: Virgil Dupras
# Created On: 2008-06-24
# Copyright 2010 Hardcoded Software (http://www.hardcoded.net)
# 
# This software is licensed under the "BSD" License as described in the "LICENSE" file, 
# which should be included with this package. The terms are also available at 
# http://www.hardcoded.net/licenses/bsd_license

import copy
import time
from datetime import date

from hscommon.testutil import eq_
from hscommon.currency import EUR

from ..const import PaneType
from ..document import ScheduleScope
from ..model.date import MonthRange
from .base import TestCase as TestCaseBase, CommonSetup, compare_apps, testdata

def copydoc(doc):
    # doing a deepcopy on the document itself makes a deepcopy of *all* guis because they're
    # listeners. What we do is a shallow copy of it, *then* a deepcopy of stuff we compare
    # afterwards.
    newdoc = copy.copy(doc)
    newdoc.accounts = copy.deepcopy(newdoc.accounts)
    newdoc.groups = copy.deepcopy(newdoc.groups)
    newdoc.transactions = copy.deepcopy(newdoc.transactions)
    newdoc.schedules = copy.deepcopy(newdoc.schedules)
    newdoc.budgets = copy.deepcopy(newdoc.budgets)
    return newdoc

class TestCase(TestCaseBase):
    """Provides an easy way to test undo/redo
    
    Set your app up and then, just before you perform the step you want to
    test undo on, call _save_state(). After you've performed your undoable
    step, call _test_undo_redo().
    """
    def _save_state(self):
        self._previous_state = copydoc(self.document)
    
    def _test_undo_redo(self):
        before_undo = copydoc(self.document)
        self.document.undo()
        compare_apps(self._previous_state, self.document)
        self.document.redo()
        compare_apps(before_undo, self.document)
    

def save_state_then_verify(testmethod):
    def wrapper(self):
        self._save_state()
        testmethod(self)
        self._test_undo_redo()
    
    wrapper.__name__ = testmethod.__name__
    return wrapper

class Pristine(TestCase):
    def setUp(self):
        self.create_instances()
    
    def test_can_redo(self):
        # can_redo is initially false.
        assert not self.document.can_redo()
    
    def test_can_undo(self):
        # can_undo is initially false.
        assert not self.document.can_undo()
    
    def test_descriptions(self):
        # undo/redo descriptions are None.
        assert self.document.undo_description() is None
        assert self.document.redo_description() is None
    
    @save_state_then_verify
    def test_undo_add_account(self):
        # Undo after an add_account() removes that account.
        self.bsheet.add_account()
    
    @save_state_then_verify
    def test_undo_add_group(self):
        # It's possible to undo the addition of an account group.
        self.bsheet.add_account_group()
    
    @save_state_then_verify
    def test_add_schedule(self):
        # schedule addition are undoable
        self.mainwindow.select_schedule_table()
        self.scpanel.new()
        self.scpanel.save()    
    
    @save_state_then_verify
    def test_add_transaction(self):
        # It's possible to undo a transaction addition (from the ttable).
        self.ttable.add()
        row = self.ttable.edited
        # make sure that aut-created accounts go away as well.
        row.from_ = 'foo'
        row.to = 'bar'
        self.ttable.save_edits()
    
    @save_state_then_verify
    def test_import(self):
        # When undoing an import that creates income/expense accounts, don't crash on auto account
        # removal
        self.document.parse_file_for_import(testdata.filepath('qif', 'checkbook.qif'))
        self.iwin.import_selected_pane()
    
    def test_undo_shown_account(self):
        # Undoing the creation of a new account when shown sets makes the main window go back to
        # the net worth sheet *before* triggering a refresh (otherwise, we crash).
        self.mainwindow.select_income_statement()
        self.mainwindow.new_item()
        self.mainwindow.show_account()
        self.document.undo() # no crash
    

class OneNamelessAccount(TestCase):
    def setUp(self):
        self.create_instances()
        self.add_account()
    
    @save_state_then_verify
    def test_undo_apanel_attrs(self):
        # Undoing a changes made from apanel work
        self.mainwindow.edit_item()
        self.apanel.currency = EUR
        self.apanel.account_number = '1234'
        self.apanel.notes = 'some notes'
        self.apanel.save()
    

class OneNamedAccount(TestCase):
    def setUp(self):
        self.create_instances()
        self.add_account('foobar')
        self.mainwindow.show_account()
    
    def test_action_after_undo(self):
        # When doing an action after an undo, the whole undo chain is broken at the current index.
        self.document.undo() # undo set name
        self.mainwindow.select_balance_sheet()
        self.bsheet.selected = self.bsheet.assets[0]
        self.bsheet.selected.name = 'foobaz'
        self.bsheet.save_edits()
        self.document.undo() # undo set name
        self.document.redo()
        eq_(self.bsheet.assets[0].name, 'foobaz')
        self.assertFalse(self.document.can_redo())
        self.document.undo()
        self.document.undo() # undo add account
        eq_(self.bsheet.assets.children_count, 2)
    
    def test_can_redo(self):
        # can_redo is false as long as an undo hasn't been performed.
        assert not self.document.can_redo()
        self.document.undo()
        assert self.document.can_redo() # now we can redo()
    
    def test_can_undo(self):
        # Now that an account has been added, can_undo() is True.
        assert self.document.can_undo()
        self.document.undo()
        self.document.undo()
        assert not self.document.can_undo()
    
    def test_change_account_on_duplicate_account_name_doesnt_record_action(self):
        # Renaming an account and causing a duplicate account name error doesn't cause an action to
        # be recorded
        self.mainwindow.select_balance_sheet()
        self.bsheet.add_account()
        self.bsheet.selected.name = 'foobar'
        self.bsheet.save_edits()
        eq_(self.document.undo_description(), 'Add account') # We're still at undoing the add
    
    def test_descriptions(self):
        # The undo/redo description system works properly.
        eq_(self.document.undo_description(), 'Change account')
        assert self.document.redo_description() is None
        self.document.undo()
        eq_(self.document.undo_description(), 'Add account')
        eq_(self.document.redo_description(), 'Change account')
        self.document.undo()
        assert self.document.undo_description() is None
        eq_(self.document.redo_description(), 'Add account')
        self.document.redo()
        eq_(self.document.undo_description(), 'Add account')
        eq_(self.document.redo_description(), 'Change account')
        self.document.redo()
        eq_(self.document.undo_description(), 'Change account')
        assert self.document.redo_description() is None
    
    def test_description_after_delete(self):
        # the undo description is 'Remove account' after deleting an account.
        self.mainwindow.select_balance_sheet()
        self.bsheet.selected = self.bsheet.assets[0]
        self.bsheet.delete()
        eq_(self.document.undo_description(), 'Remove account')
    
    def test_gui_calls(self):
        # the correct gui calls are made when undoing/redoing (in particular: stop_editing)
        self.mainwindow.select_balance_sheet()
        self.clear_gui_calls()
        self.document.undo()
        self.check_gui_calls(self.bsheet_gui, ['refresh', 'stop_editing'])
        self.document.redo()
        self.check_gui_calls(self.bsheet_gui, ['refresh', 'stop_editing'])
    
    def test_modified_status(self):
        filepath = str(self.tmppath() + 'foo.moneyguru')
        self.document.save_to_xml(filepath)
        assert not self.document.is_dirty()
        self.add_entry()
        assert self.document.is_dirty()
        self.document.undo()
        assert not self.document.is_dirty()
        self.document.redo()
        assert self.document.is_dirty()
        self.document.undo()
        assert not self.document.is_dirty()
        self.document.undo()
        assert self.document.is_dirty()
        self.document.redo()
        assert not self.document.is_dirty()
        self.document.undo()
        self.document.undo()
        assert self.document.is_dirty()
    
    def test_redo_delete_while_in_etable(self):
        # If we're in etable and perform a redo that removes the account we're in, go back to the bsheet
        self.mainwindow.select_balance_sheet()
        self.bsheet.selected = self.bsheet.assets[0]
        self.bsheet.delete()
        self.document.undo()
        self.bsheet.selected = self.bsheet.assets[0]
        self.bsheet.show_selected_account()
        self.clear_gui_calls()
        self.document.redo()
        self.ta.check_current_pane(PaneType.NetWorth)
        expected = ['view_closed', 'change_current_pane', 'refresh_undo_actions', 'refresh_status_line']
        self.check_gui_calls(self.mainwindow_gui, expected)
    
    @save_state_then_verify
    def test_undo_add_entry(self):
        # Undoing an entry addition works in one shot (not one shot to blank the fields then one 
        # other shot to remove the transaction.
        self.add_entry(description='foobar')
    
    @save_state_then_verify
    def test_undo_delete_account(self):
        # Undo after having removed an account puts it back in.
        self.mainwindow.select_balance_sheet()
        self.bsheet.selected = self.bsheet.assets[0]
        self.bsheet.delete()
    
    @save_state_then_verify
    def test_undo_move_account(self):
        # Moving an account from one section to another can be undone
        self.mainwindow.select_balance_sheet()
        self.bsheet.move([0, 0], [1])

    @save_state_then_verify
    def test_undo_set_account_name(self):
        # Undo after a name change puts back the old name.
        self.mainwindow.select_balance_sheet()
        self.bsheet.selected = self.bsheet.assets[0]
        self.bsheet.selected.name = 'foobaz'
        self.bsheet.save_edits()
    
    def test_undo_add_while_in_etable(self):
        # If we're in etable and perform an undo that removes the account we're in, go back to the bsheet
        self.mainwindow.select_entry_table()
        self.document.undo()
        self.clear_gui_calls()
        self.document.undo()
        self.ta.check_current_pane(PaneType.NetWorth)
        expected = ['view_closed', 'change_current_pane', 'refresh_undo_actions', 'refresh_status_line']
        self.check_gui_calls(self.mainwindow_gui, expected)
    
    def test_undo_twice(self):
        # Undoing a new_account() just after having undone a change_account works.
        # Previously, a copy of the changed account would be inserted, making it impossible for
        # undo to find the account to be removed.
        self.mainwindow.select_balance_sheet()
        self.document.undo()
        self.document.undo()
        eq_(self.bsheet.assets.children_count, 2)
    

class OneAccountGroup(TestCase):
    def setUp(self):
        self.create_instances()
        self.add_group()
    
    def test_descriptions(self):
        # All group descriptions are there.
        eq_(self.document.undo_description(), 'Add group')
        self.bsheet.selected = self.bsheet.assets[0]
        self.bsheet.selected.name = 'foobar'
        self.bsheet.save_edits()
        eq_(self.document.undo_description(), 'Change group')
        self.bsheet.delete()
        eq_(self.document.undo_description(), 'Remove group')
    
    @save_state_then_verify
    def test_undo_delete_group(self):
        # It's possible to undo group deletion.
        self.mainwindow.select_balance_sheet()
        self.bsheet.selected = self.bsheet.assets[0]
        self.bsheet.delete()
    
    @save_state_then_verify
    def test_undo_rename_group(self):
        # It's possible to undo a group rename.
        self.mainwindow.select_balance_sheet()
        self.bsheet.selected = self.bsheet.assets[0]
        self.bsheet.selected.name = 'foobar'
        self.bsheet.save_edits()
    

class AccountInGroup(TestCase):
    def setUp(self):
        self.create_instances()
        self.add_group('group')
        self.add_account(group_name='group')
        self.mainwindow.show_account()
    
    def test_change_group_on_duplicate_account_name_doesnt_record_action(self):
        # Renaming a group and causing a duplicate account name error doesn't cause an action to
        # be recorded
        self.mainwindow.select_balance_sheet()
        self.bsheet.add_account_group()
        self.bsheet.selected.name = 'group'
        self.bsheet.save_edits()
        eq_(self.document.undo_description(), 'Add group') # We're still at undoing the add
    
    @save_state_then_verify
    def test_undo_delete_group(self):
        # When undoing a group deletion, the accounts that were in it are back in.
        self.mainwindow.select_balance_sheet()
        self.bsheet.selected = self.bsheet.assets[0]
        self.bsheet.delete()
    
    @save_state_then_verify
    def test_undo_move_account_out_of_group(self):
        # Undoing a move_account for an account that was in a group puts it back in that group.
        self.mainwindow.select_balance_sheet()
        self.bsheet.move([0, 0, 0], [1])
    

class LoadFile(TestCase):
    # Loads 'simple.moneyguru', a file with 2 accounts and 2 entries in each. Select the first entry.
    def setUp(self):
        self.create_instances()
        self.document.date_range = MonthRange(date(2008, 2, 1))
        # This is to set the modified flag to true so we can make sure it has been put back to false
        self.add_account()
        self.document.load_from_xml(testdata.filepath('moneyguru', 'simple.moneyguru'))
        # we have to cheat here because the first save state is articifially
        # different than the second save state because the second state has
        # the currency rates fetched. So what we do here is wait a little bit
        # and recook.
        time.sleep(0.05)
        self.document._cook()
        self.mainwindow.select_balance_sheet()
        self.bsheet.selected = self.bsheet.assets[0]
        self.bsheet.show_selected_account()
    
    def test_can_undo(self):
        # can_undo becomes false after a load.
        assert not self.document.can_undo()
    
    @save_state_then_verify
    def test_undo_add_account(self):
        # The undoer keeps its account list up-to-date after a load.
        # Previously, the Undoer would hold an old instance of AccountList
        self.bsheet.add_account()
    
    @save_state_then_verify
    def test_undo_add_entry(self):
        # The undoer keeps its transaction list up-to-date after a load.
        # Previously, the Undoer would hold an old instance of TransactionList
        self.add_entry(description='foobar', transfer='some_account', increase='42')
    
    @save_state_then_verify
    def test_undo_add_group(self):
        # The undoer keeps its group list up-to-date after a load.
        # Previously, the Undoer would hold an old instance of GroupList
        self.mainwindow.select_balance_sheet()
        self.bsheet.add_account_group()
    

class TwoAccountsTwoTransactions(TestCase):
    # 2 accounts, 1 transaction that is a transfer between the 2 accounts, and 1 transaction that
    # is imbalanced.
    def setUp(self):
        self.create_instances()
        self.add_account('first')
        self.add_account('second')
        self.show_account('first')
        self.add_entry('19/6/2008', transfer='second')
        self.add_entry('20/6/2008', description='description', payee='payee', increase='42', checkno='12')
    
    def test_descriptions(self):
        # All transaction descriptions are there.
        eq_(self.document.undo_description(), 'Add transaction')
        row = self.etable.selected_row
        row.description = 'foobar'
        self.etable.save_edits()
        eq_(self.document.undo_description(), 'Change transaction')
        self.etable.delete()
        eq_(self.document.undo_description(), 'Remove transaction')
    
    def test_etable_refreshes(self):
        self.clear_gui_calls()
        self.document.undo()
        eq_(self.ta.etable_count(), 1)
        self.check_gui_calls(self.etable_gui, ['refresh', 'stop_editing'])
    
    def test_ttable_refreshes(self):
        self.mainwindow.select_transaction_table()
        self.clear_gui_calls()
        self.document.undo()
        eq_(self.ttable.row_count, 1)
        self.check_gui_calls(self.ttable_gui, ['refresh', 'stop_editing'])
    
    @save_state_then_verify
    def test_undo_change_transaction_from_etable(self):
        # It's possible to undo a transaction change.
        row = self.etable.selected_row
        row.date = '21/6/2008'
        row.description = 'foo'
        row.payee = 'baz'
        row.transfer = 'third'
        row.decrease = '34'
        row.checkno = '15'
        self.etable.save_edits()
    
    @save_state_then_verify
    def test_undo_change_transaction_from_ttable(self):
        # It's possible to undo a transaction change.
        self.mainwindow.select_transaction_table()
        row = self.ttable[1]
        row.date = '21/6/2008'
        row.description = 'foo'
        row.payee = 'baz'
        row.from_ = 'third'
        row.to = 'fourth'
        row.amount = '34'
        row.checkno = '15'
        self.ttable.save_edits()
    
    @save_state_then_verify
    def test_undo_delete_entry(self):
        # It's possible to undo a transaction deletion.
        self.etable.select([0, 1])
        self.etable.delete()
    
    @save_state_then_verify
    def test_undo_delete_transaction(self):
        # It's possible to undo a transaction deletion.
        self.mainwindow.select_transaction_table()
        self.ttable.select([0, 1])
        self.ttable.delete()
    
    @save_state_then_verify
    def test_undo_delete_account(self):
        # When 'first' is deleted, one transaction is simply unbound, and the other is deleted. we 
        # must undo all that
        self.mainwindow.select_balance_sheet()
        self.bsheet.selected = self.bsheet.assets[0]
        self.bsheet.delete()
        self.arpanel.save() # continue deletion
    
    @save_state_then_verify
    def test_undo_duplicate_transaction(self):
        self.mainwindow.select_transaction_table()
        self.ttable.select([0, 1])
        self.ttable.duplicate_selected()
    
    @save_state_then_verify
    def test_undo_mass_edition(self):
        # Mass edition can be undone.
        self.etable.select([0, 1])
        self.mepanel.load()
        self.mepanel.description_enabled = True
        self.mepanel.description = 'foobar'
        self.mepanel.save()
    
    @save_state_then_verify
    def test_undo_schedule(self):
        self.tpanel.load()
        self.tpanel.repeat_index = 1 # daily
        self.tpanel.save()
    
    def test_undo_schedule_entry_transfer(self):
        # After undoing a scheduling, the entry has the wrong transfer
        self.etable.select([0])
        self.tpanel.load()
        self.tpanel.repeat_index = 1 # daily
        self.tpanel.save()
        self.document.undo()
        eq_(self.etable[0].transfer, 'second')
    

class TwoTransactionsSameDate(TestCase):
    def setUp(self):
        self.create_instances()
        self.add_account()
        self.mainwindow.show_account()
        self.add_entry('19/6/2008', description='first')
        self.add_entry('19/6/2008', description='second')
    
    @save_state_then_verify
    def test_undo_delete_first_transaction(self):
        # When undoing a deletion, the entry comes back at the same position.
        self.etable.select([0])
        self.etable.delete()
    
    @save_state_then_verify
    def test_undo_reorder_entry(self):
        # Reordering can be undone.
        self.etable.move([1], 0)
    

class ThreeTransactionsReconciled(TestCase):
    def setUp(self):
        self.create_instances()
        self.add_account()
        self.mainwindow.show_account()
        self.add_entry('19/6/2008', description='first')
        self.add_entry('19/6/2008', description='second')
        self.add_entry('20/6/2008', description='third')
        self.aview.toggle_reconciliation_mode()
        self.etable[0].toggle_reconciled()
        self.etable[1].toggle_reconciled()
        self.etable[2].toggle_reconciled()
        self.aview.toggle_reconciliation_mode() # commit
    
    @save_state_then_verify
    def test_change_entry(self):
        # Performing a txn change that results in unreconciliation can be completely undone
        # (including the unreconciliation).
        self.mainwindow.select_balance_sheet()
        self.bsheet.selected = self.bsheet.assets[0]
        self.bsheet.show_selected_account()
        self.etable[0].date = '18/6/2008'
        self.etable.save_edits()
    
    @save_state_then_verify
    def test_change_transaction(self):
        # Performing a txn change that results in unreconciliation can be completely undone
        # (including the unreconciliation).
        self.mainwindow.select_transaction_table()
        self.ttable[0].date = '18/6/2008'
        self.ttable.save_edits()
    
    @save_state_then_verify
    def test_delete_transaction(self):
        # Deleting txn change that results in unreconciliation can be completely undone
        # (including the unreconciliation).
        self.mainwindow.select_transaction_table()
        self.ttable.delete()
    
    @save_state_then_verify
    def test_move_transaction(self):
        # Moving txn change that results in unreconciliation can be completely undone
        # (including the unreconciliation).
        self.mainwindow.select_transaction_table()
        self.ttable.move([0], 2)
    
    @save_state_then_verify
    def test_toggle_reconciled(self):
        # reconciliation toggling is undoable
        self.aview.toggle_reconciliation_mode()
        self.etable[1].toggle_reconciled()
    

class OFXImport(TestCase):
    def setUp(self):
        self.create_instances()
        self.document.date_range = MonthRange(date(2008, 2, 1))
        self.document.parse_file_for_import(testdata.filepath('ofx', 'desjardins.ofx'))
        self.iwin.import_selected_pane()
        # same cheat as in LoadFile
        time.sleep(0.05)
        self.document._cook()
        self.mainwindow.select_balance_sheet()
        self.bsheet.selected = self.bsheet.assets[0]
        self.bsheet.show_selected_account()
    
    def test_description(self):
        # The undo description is 'Import'.
        eq_(self.document.undo_description(), 'Import')
    
    @save_state_then_verify
    def test_undo_delete_transaction(self):
        # When undoing a transaction's deletion which had a reference, actually put it back in.
        # Previously, the reference stayed in the dictionary, making it as if
        # the transaction was still there
        self.etable.delete()
    
    @save_state_then_verify
    def test_undo_import(self):
        # Undoing an import removes all accounts and transactions added by  that import. It also
        # undo changes that have been made.
        self.document.parse_file_for_import(testdata.filepath('ofx', 'desjardins2.ofx'))
        # this is the pane that has stuff in it
        self.iwin.selected_target_account_index = 1
        self.iwin.import_selected_pane()
    

class TransactionWithAutoCreatedTransfer(TestCase):
    def setUp(self):
        self.create_instances()
        self.add_account()
        self.mainwindow.show_account()
        self.add_entry('19/6/2008', transfer='auto')
    
    @save_state_then_verify
    def test_undo_delete_transaction_brings_back_auto_created_account(self):
        # When undoing the deletion of a transaction that results in the removal of an
        # income/expense account, bring that account back.
        self.etable.delete()
    

class ScheduledTransaction(TestCase):
    def setUp(self):
        self.create_instances()
        self.add_account('account')
        self.add_schedule(description='foobar', account='account')
        self.mainwindow.select_schedule_table()
        self.sctable.select([0])
    
    @save_state_then_verify
    def test_change_schedule(self):
        self.scpanel.load()
        self.scpanel.description = 'changed'
        self.scpanel.repeat_every = 12
        self.scpanel.save()
    
    def test_change_spawn_globally(self):
        # Changing a spawn globally then undoing correcty updates the spawns. Old values would
        # previously linger around even though the schedule had been un-changed.
        self.mainwindow.select_transaction_table()
        self.document_gui.query_for_schedule_scope_result = ScheduleScope.Global
        self.ttable.select([0])
        self.ttable[0].description = 'changed'
        self.ttable.save_edits()
        self.document.undo()
        eq_(self.ttable[1].description, 'foobar')
    
    @save_state_then_verify
    def test_delete_account(self):
        self.mainwindow.select_balance_sheet()
        self.bsheet.selected = self.bsheet.assets[0]
        self.bsheet.delete()
        self.arpanel.save()
    
    @save_state_then_verify
    def test_delete_schedule(self):
        self.sctable.delete()
    
    def test_delete_spawn_undo_then_delete_again(self):
        # There was a bug where a spawn deletion being undone would result in an undeletable spawn
        # being put back into the ttable.
        self.mainwindow.select_transaction_table()
        self.ttable.select([0])
        self.ttable.delete()
        self.document.undo()
        # we don't care about the exact len, we just care that it decreases by 1
        len_before = self.ttable.row_count
        self.ttable.select([0])
        self.ttable.delete()
        eq_(self.ttable.row_count, len_before-1)
    
    @save_state_then_verify
    def test_reconcile_spawn_by_changing_recdate(self):
        # Undoing a spawn reconciliation correctly removes the materialized txn.
        self.show_account('account')
        self.etable[0].reconciliation_date = self.etable[0].date
        self.etable.save_edits()
    
    @save_state_then_verify
    def test_reconcile_spawn_by_toggling(self):
        # Undoing a spawn reconciliation correctly removes the materialized txn.
        self.show_account('account')
        self.aview.toggle_reconciliation_mode()
        self.etable[0].toggle_reconciled()
    

class Budget(TestCase, CommonSetup):
    def setUp(self):
        self.create_instances()
        self.setup_account_with_budget()
        self.mainwindow.select_budget_table()
        self.btable.select([0])
    
    @save_state_then_verify
    def test_change_budget(self):
        self.bpanel.load()
        self.bpanel.repeat_every = 12
        self.bpanel.save()
    
    @save_state_then_verify
    def test_delete_account(self):
        self.mainwindow.select_income_statement()
        self.istatement.selected = self.istatement.expenses[0]
        self.istatement.delete()
        self.arpanel.save()
    
    @save_state_then_verify
    def test_delete_budget(self):
        self.btable.delete()
    
