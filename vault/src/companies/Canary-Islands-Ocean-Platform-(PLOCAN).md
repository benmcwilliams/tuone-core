```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Canary-Islands-Ocean-Platform-(PLOCAN)" or company = "Canary Islands Ocean Platform (PLOCAN)")
sort location, dt_announce desc
```
