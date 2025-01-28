```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Wystrach-GmbH" or company = "Wystrach GmbH")
sort location, dt_announce desc
```
