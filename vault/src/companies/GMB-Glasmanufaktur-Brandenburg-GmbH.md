```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "GMB-Glasmanufaktur-Brandenburg-GmbH" or company = "GMB Glasmanufaktur Brandenburg GmbH")
sort location, dt_announce desc
```
