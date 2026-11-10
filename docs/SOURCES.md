# Seed source audit — November 10, 2026

The supplied 43-event list is the starting dataset. Ten records are confirmed at event level; all others remain unverified. Unknown admission prices are not treated as free. Official sources below support the facts embedded in `data/seed.json`. Other organizer URLs are attached when found even if a dated schedule remains unresolved.

| Event | Official source | Findings |
| --- | --- | --- |
| Canton Tree Lighting | https://explorecantonga.com/events/city-of-canton-tree-lighting-and-drone-show/ | November 18, 6:30–8:30 pm; Cannon Park, 130 E Main St. Price unstated. |
| Alpharetta Season of Celebration | https://www.awesomealpharetta.com/christmas-tree-lighting/ and https://exploregeorgia.org/alpharetta/events/entertainment/season-of-celebration | November 21, 5–8 pm; Village Green, 2 Park Plaza. State tourism listing identifies free admission. |
| Lighting of Avalon | https://www.awesomealpharetta.com/event/the-lighting-of-avalon/ | November 22, 2–7:30 pm; Avalon, 400 Avalon Blvd. Individual activity prices not assumed. |
| Woodstock Christmas Jubilee | https://woodstock.recdesk.com/Community/Program/Detail?programId=2646 | December 6, festival 2–5 pm, parade starts 5:30 pm. Combined record has no assumed closing time. |
| Atlanta Pops Christmas | https://atlantapops.org/concerts-events/ | November 30, 3 pm and 7:30 pm; Falany, 199 Fine Arts Drive. |
| A Christmas Carol: The Musical | https://woodstockarts.org/events/a-christmas-carol-2026/ | Twelve listed performances Dec 4–24, with exact start times; online $21–22 and door $23–25; 8534 Main St. Dec 10 requires contacting theatre. |
| Georgia Symphony Holiday Pops | https://www.georgiasymphony.org/event/holiday-pops-4/ and https://www.georgiasymphony.org/event/holiday-pops-5/ | Dec 5, 7:30–9:30 pm ($20–65); Dec 6, 3–5 pm ($15–49.50); Marietta Performing Arts Center. |
| Kennesaw Tree Lighting | https://www.kennesaw-ga.gov/kennesaw-event/annual-tree-lighting-ceremony-2/ | December 2, 6–7:30 pm; Depot Park. |
| Kennesaw Glimmer & Glee | https://www.kennesaw-ga.gov/kennesaw-event/glimmer-glee-drone-show/ | December 13, 6–8 pm; drone display 7:30 pm; Depot Park. |
| Kennesaw Holiday Extravaganza | https://www.kennesaw-ga.gov/kennesaw-celebrates-the-holiday-season-with-annual-holly-days-events/ | November 29–January 10, 2027; Depot Park; daily access hours not stated. |

Additional venue address evidence:

- The Mill: https://explorecantonga.com/events/annual-events/ — 225 Reformation Parkway.
- The Park at City Center: https://woodstock.recdesk.com/Community/Page?pageId=27835 — 101 Arnold Mill Rd.
- Depot Park: https://www.kennesaw-ga.gov/parks-and-recreation/depot-park/ — 2828 Cherokee Street NW.
- Marietta Performing Arts Center: https://www.georgiasymphony.org/venues/ — 1171 Whitlock Ave NW.

Partial checks retained as unverified:

- Nashville Noel official ticketing page https://thefalany.showare.com/eventperformances.asp?evt=9 confirms the show/venue but its date loads dynamically and was not confirmed in the source text.
- Kennesaw city notifications confirm Dec 5 parade at 6 pm, but the entire combined Day with Santa record is not yet checked.
- Awesome Alpharetta's annual calendar mentions 2026 Lights on the Loop and Avalon on Ice; precise operating days/hours remain unresolved in the seed.
- Older Canton annual overview text mentions a different tree-lighting date; the specific 2026 event page takes precedence for the confirmed Canton record.

Coordinates are actual OpenStreetMap Nominatim address-search results, cached in seed venues with returned display-name provenance. Address matches can represent a building, street or entrance rather than an event footprint. They should be checked and manually corrected where necessary. No missing event location is replaced with a town-center guess. The regional map center is not an event location.

`make_seed.py` transcribes the supplied list and `enrich_seed.py` records the findings above. These are research provenance tools, not an application startup path: regenerating the seed removes one-time geocoding enrichment unless it is preserved separately. Use the checked-in seed directly for installation. Do not regenerate it to update existing administrator-managed data.
