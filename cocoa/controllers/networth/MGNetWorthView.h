/* 
Copyright 2010 Hardcoded Software (http://www.hardcoded.net)

This software is licensed under the "HS" License as described in the "LICENSE" file, 
which should be included with this package. The terms are also available at 
http://www.hardcoded.net/licenses/hs_license
*/

#import <Cocoa/Cocoa.h>
#import "PyNetWorthView.h"
#import "MGBaseView.h"
#import "MGDocument.h"
#import "MGOutlineView.h"
#import "MGBalanceSheet.h"
#import "MGPieChart.h"
#import "MGBalanceGraph.h"
#import "MGDoubleView.h"

@interface MGNetWorthView : MGBaseView
{
    IBOutlet MGOutlineView *outlineView;
    IBOutlet NSScrollView *outlineScrollView;
    IBOutlet MGDoubleView *pieChartsView;
    IBOutlet NSView *netWorthGraphPlaceholder;
    
    PyNetWorthView *py;
    MGBalanceSheet *balanceSheet;
    MGPieChart *assetsPieChart;
    MGPieChart *liabilitiesPieChart;
    MGBalanceGraph *netWorthGraph;
}
- (id)initWithDocument:(MGDocument *)aDocument;
- (PyNetWorthView *)py;

/* Private */
- (void)updateVisibility;
@end