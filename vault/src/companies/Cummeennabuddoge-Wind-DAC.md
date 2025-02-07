```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Cummeennabuddoge-Wind-DAC" or company = "Cummeennabuddoge Wind DAC")
sort location, dt_announce desc
```
