```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Geothermie-Rupertiwinkel-GmbH" or company = "Geothermie Rupertiwinkel GmbH")
sort location, dt_announce desc
```
