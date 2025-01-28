```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Tenten-Solar-Zonnepanelen-B.V." or company = "Tenten Solar Zonnepanelen B.V.")
sort location, dt_announce desc
```
