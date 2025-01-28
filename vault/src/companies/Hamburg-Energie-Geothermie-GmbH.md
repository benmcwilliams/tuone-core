```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Hamburg-Energie-Geothermie-GmbH" or company = "Hamburg Energie Geothermie GmbH")
sort location, dt_announce desc
```
