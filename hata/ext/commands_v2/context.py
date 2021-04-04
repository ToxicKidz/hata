# -*- coding: utf-8 -*-

__slots__ = ('CommandContext', )

class CommandContext(object):
    """
    Represents a command context within the command is invoked.
    
    Attributes
    ----------
    client : ``Client``
        The client who received the message.
    command : ``Command``
        The command to invoke.
    content : `str`
        The message's content after prefix.
    message : ``Message``
        The received message.
    parameters : `None` or `dict` of (`str`, `Any`)
        The parsed parameters.
    prefix : `None` or `str`
        The prefix used when calling the command.
    """
    __slots__ = ('client', 'command', 'content', 'message', 'parameters', 'prefix')
    
    def __new__(cls, client, message, prefix, content, command):
        """
        Creates a new command context instance.
        
        client : ``Client``
            The client who received the message.
        message : ``Message``
            The received message.
        prefix : `str` or `None`
            The matched prefix.
        content : `str`
            The message's content after prefix.
        command : ``Command``
            The command to invoke.
        """
        self = object.__new__(cls)
        self.client = client
        self.message = message
        self.parameters = None
        self.prefix = prefix
        self.content = content
        self.command = command
        return self
    
    def __repr__(self):
        """Returns teh context's representation."""
    
    # Properties
    
    @property
    def channel(self):
        """
        Returns the message's channel.
        
        Returns
        -------
        channel : ``ChannelBase``
        """
        return self.message.channel
    
    @property
    def guild(self):
        """
        Returns the message's guild.
        
        Returns
        -------
        guild : `None` or ``Guild``
        """
        return self.message.channel.guild
    
    
    @property
    def author(self):
        """
        Returns the message's author.
        
        Returns
        -------
        author : ``User``, ``Client``, ``Webhook``, ``WebhookRepr``
        """
        return self.message.author
    
    @property
    def voice_client(self):
        """
        Returns the voice client in the message's guild if there is any.
        
        Returns
        -------
        voice_client : `None` or ``VoiceClient``
        """
        guild = self.message.chanenl.guild
        if guild is None:
            voice_client = None
        else:
            voice_client = self.client.voice_clients.get(guild.id)
        
        return voice_client
    
    # API methods
    
    async def reply(self, *args, **kwargs):
        """
        Replies to teh command's caller.
        
        This method is a coroutine.
        
        Parameters
        ----------
        content : `str`, ``EmbedBase``, `Any`, Optional
            The message's content if given. If given as `str` or empty string, then no content will be sent, meanwhile
            if any other non `str` or ``EmbedBase`` instance is given, then will be casted to string.
            
            If given as ``EmbedBase`` instance, then is sent as the message's embed.
            
        embed : ``EmbedBase`` instance or `list` of ``EmbedBase`` instances, Optional
            The embedded content of the message.
            
            If `embed` and `content` parameters are both given as  ``EmbedBase`` instance, then `TypeError` is raised.
            
            If embeds are given as a list, then the first embed is picked up.
        file : `Any`, Optional
            A file or files to send. Check ``._create_file_form`` for details.
        sticker : `None`, ``Sticker``, `int`, (`list`, `set`, `tuple`) of (``Sticker``, `int`)
            Sticker or stickers to send within the message.
        allowed_mentions : `None`,  `str`, ``UserBase``, ``Role``, `list` of (`str`, ``UserBase``, ``Role`` ), Optional
            Which user or role can the message ping (or everyone). Check ``._parse_allowed_mentions`` for details.
        reply_fail_fallback : `bool`, Optional
            Whether normal message should be sent if the referenced message is deleted. Defaults to `False`.
        tts : `bool`, Optional
            Whether the message is text-to-speech.
        nonce : `str`, Optional
            Used for optimistic message sending. Will shop up at the message's data.
        
        Returns
        -------
        message : ``Message`` or `None`
            Returns `None` if there is nothing to send.
        
        Raises
        ------
        TypeError
            - If `embed` was given as `list`, but it contains not only ``EmbedBase`` instances.
            - If `allowed_mentions` contains an element of invalid type.
            - `content` parameter was given as ``EmbedBase`` instance, meanwhile `embed` parameter was given as well.
            - If invalid file type would be sent.
            - If `sticker` was not given neither as `None`, ``Sticker``, `int`, (`list`, `tuple`, `set`) of \
                (``Sticker``, `int).
        ValueError
            - If `allowed_mentions`'s elements' type is correct, but one of their value is invalid.
            - If more than `10` files would be sent.
        ConnectionError
            No internet connection.
        DiscordException
            If any exception was received from the Discord API.
        AssertionError
            - If `tts` was not given as `bool` instance.
            - If `nonce` was not given neither as `None` nor as `str` instance.
            - If `reply_fail_fallback` was not given as `bool` instance.
        """
        return await self.client.message_create(self.message, *args, **kwargs)
        
    
    async def send(self, *args, **kwargs):
        """
        Sends a message to the channel.
        
        This method is a coroutine.
        
        Parameters
        ----------
        content : `str`, ``EmbedBase``, `Any`, Optional
            The message's content if given. If given as `str` or empty string, then no content will be sent, meanwhile
            if any other non `str` or ``EmbedBase`` instance is given, then will be casted to string.
            
            If given as ``EmbedBase`` instance, then is sent as the message's embed.
            
        embed : ``EmbedBase`` instance or `list` of ``EmbedBase`` instances, Optional
            The embedded content of the message.
            
            If `embed` and `content` parameters are both given as  ``EmbedBase`` instance, then `TypeError` is raised.
            
            If embeds are given as a list, then the first embed is picked up.
        file : `Any`, Optional
            A file or files to send. Check ``._create_file_form`` for details.
        sticker : `None`, ``Sticker``, `int`, (`list`, `set`, `tuple`) of (``Sticker``, `int`)
            Sticker or stickers to send within the message.
        allowed_mentions : `None`,  `str`, ``UserBase``, ``Role``, `list` of (`str`, ``UserBase``, ``Role`` ), Optional
            Which user or role can the message ping (or everyone). Check ``._parse_allowed_mentions`` for details.
        reply_fail_fallback : `bool`, Optional
            Whether normal message should be sent if the referenced message is deleted. Defaults to `False`.
        tts : `bool`, Optional
            Whether the message is text-to-speech.
        nonce : `str`, Optional
            Used for optimistic message sending. Will shop up at the message's data.
        
        Returns
        -------
        message : ``Message`` or `None`
            Returns `None` if there is nothing to send.
        
        Raises
        ------
        TypeError
            - If `embed` was given as `list`, but it contains not only ``EmbedBase`` instances.
            - If `allowed_mentions` contains an element of invalid type.
            - `content` parameter was given as ``EmbedBase`` instance, meanwhile `embed` parameter was given as well.
            - If invalid file type would be sent.
            - If `sticker` was not given neither as `None`, ``Sticker``, `int`, (`list`, `tuple`, `set`) of \
                (``Sticker``, `int).
        ValueError
            - If `allowed_mentions`'s elements' type is correct, but one of their value is invalid.
            - If more than `10` files would be sent.
        ConnectionError
            No internet connection.
        DiscordException
            If any exception was received from the Discord API.
        AssertionError
            - If `tts` was not given as `bool` instance.
            - If `nonce` was not given neither as `None` nor as `str` instance.
            - If `reply_fail_fallback` was not given as `bool` instance.
        """
        return await self.client.message_create(self.message.channel, *args, **kwargs)
    
    
    async def trigger_typing(self):
        """
        Triggers typing indicator in the channel.
        
        This method is a coroutine.
        
        Raises
        ------
        TypeError
            If `channel` was not given neither as ``ChannelTextBase`` nor `int` instance.
        ConnectionError
            No internet connection.
        DiscordException
            If any exception was received from the Discord API.
        
        Notes
        -----
        The client will be shown up as typing for 8 seconds, or till it sends a message at the respective channel.
        """
        return await self.client.typing(self.channel)
    
    
    def typing(self, *args, **kwargs):
        """
        Returns a context manager which will keep sending typing events at the channel. Can be used to indicate that
        the bot is working.
        
        Parameters
        ----------
        timeout : `float`, Optional
            The maximal duration for the ``Typer`` to keep typing.
        
        Returns
        -------
        typer : ``Typer``
        
        Examples
        --------
        ```py
        with ctx.typing():
            # Do some things
            await ctx.send('Ayaya')
        ```
        """
        return self.client.keep_typing(self.channel, *args, **kwargs)
