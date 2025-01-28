```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Ministry-of-Climate-of-Estonia" or company = "Ministry of Climate of Estonia")
sort location, dt_announce desc
```
