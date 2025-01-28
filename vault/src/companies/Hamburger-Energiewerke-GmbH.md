```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Hamburger-Energiewerke-GmbH" or company = "Hamburger Energiewerke GmbH")
sort location, dt_announce desc
```
