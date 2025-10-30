class CogsBase:
    async def initialize(self) -> None:
        """
        A function to setup the Cog before starting the bot.
        Raise a CriticalCogInitializationError exception if the cog cannot be initialized.
        Raise a NonCriticalCogInitializationError exception if the cog can be initialized in a degraded mode.
        All other exceptions will be treated as critical.
        :return:
        """
        pass
