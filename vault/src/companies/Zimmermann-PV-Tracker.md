```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Zimmermann-PV-Tracker" or company = "Zimmermann PV Tracker")
sort location, dt_announce desc
```
