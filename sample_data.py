"""
Sample data for the GTIN Validator — simulates a messy product master
from a ~$25M specialty food manufacturer.
"""

SAMPLE_DATA = """GTIN,Product Name
614141000012,Roasted Garlic Marinara 24oz
614141000029,Spicy Arrabbiata Sauce 24oz
614141000036,Classic Basil Pesto 8oz
614141000043,Sun-Dried Tomato Spread 12oz
614141000050,Lemon Herb Vinaigrette 16oz
614141000067,Balsamic Glaze 8.5oz
614141000074,Roasted Red Pepper Sauce 24oz
614141000081,Truffle Mushroom Sauce 12oz
614141000098,Calabrian Chili Sauce 8oz
61414100010,Hot Honey Drizzle 12oz
614141000111,Smoked Paprika Aioli 8oz
614141000128,Everything Bagel Seasoning 4oz
614141000135,Italian Herb Blend 3oz
614141000142,Garlic Confit Spread 6oz
614141000159,Artichoke Tapenade 8oz
614141000166,Olive Oil Infusion Rosemary 16oz
614141000173,Olive Oil Infusion Lemon 16oz
614141000180,Olive Oil Infusion Garlic 16oz
614141000197,Roasted Garlic Marinara 12oz (Club Size)
614141000197,Roasted Garlic Marinara CASE
614141000203,Spicy Arrabbiata Sauce 12oz
614141000210,Bruschetta Topping 12oz
614141000227,Romesco Sauce 12oz
614141000234,Chimichurri 8oz
614141000241,Green Goddess Dressing 16oz
614141000258,Caesar Dressing 16oz
614141000265,Ranch Dressing 16oz
614141000272,Honey Mustard 12oz
614141000289,BBQ Sauce Sweet 18oz
614141000296,BBQ Sauce Smoky 18oz
614141000302,BBQ Sauce Spicy 18oz
614141000319,Teriyaki Glaze 16oz
614141000326,Korean Gochujang Sauce 8oz
614141000333,Thai Sweet Chili Sauce 12oz
614141000340,Mango Habanero Hot Sauce 5oz
614141000356,Ghost Pepper Hot Sauce 5oz
10614141000019,Roasted Garlic Marinara CASE (12ct)
10614141000026,Spicy Arrabbiata CASE (12ct)
10614141000033,Classic Basil Pesto CASE (12ct)
614141000364,Chipotle Mayo 8oz
732141000018,Organic Agave Nectar 16oz
732141000025,Organic Maple Syrup 12oz
614141000371,Roasted Garlic Marinara 24oz (WF)
000000000000,PLACEHOLDER - NEW PRODUCT TBD
6141410003A5,Seasonal Gift Set Holiday
614141000043,Sun-Dried Tomato Spread 12oz REPACK
"""

SAMPLE_DESCRIPTION = """
**About this sample data:**

This simulates a real-world product master from a ~$25M specialty food
manufacturer with ~40 SKUs across multiple product lines. The data
intentionally contains common issues found at companies this size:

- **Bad check digits** — from manual data entry errors
- **Truncated GTINs** — spreadsheet stripped a leading zero
- **Duplicates** — same GTIN used for different items
- **Non-numeric characters** — from copy/paste errors
- **All-zeros placeholder** — item planned but not set up
- **Mixed company prefixes** — from an acquisition
- **Case GTINs (GTIN-14)** — some present, most missing
- **Orphan case GTINs** — case GTIN without matching unit

This is what "we grew faster than our data systems" looks like in practice.
"""
