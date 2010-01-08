/* 
Copyright 2010 Hardcoded Software (http://www.hardcoded.net)

This software is licensed under the "HS" License as described in the "LICENSE" file, 
which should be included with this package. The terms are also available at 
http://www.hardcoded.net/licenses/hs_license
*/

#import <Cocoa/Cocoa.h>
#import "MGGUIControllerBase.h"
#import "MGDocument.h"
#import "MGTableView.h"
#import "MGBudgetTable.h"

@interface MGBudgetView : MGGUIControllerBase
{
    IBOutlet MGTableView *tableView;
    IBOutlet NSView *wholeView;
    
    MGBudgetTable *budgetTable;
}
- (id)initWithDocument:(MGDocument *)aDocument;

// Temporary
- (MGBudgetTable *)budgetTable;
@end